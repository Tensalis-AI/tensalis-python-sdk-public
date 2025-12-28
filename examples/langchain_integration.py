# examples/langchain_integration.py
"""
Example: Integrating Tensalis with LangChain RAG pipelines.

This example demonstrates how to add hallucination detection
to your existing LangChain applications.
"""

from typing import List, Optional
from tensalis import TensalisClient, TensalisAPIError

# Initialize the Tensalis guard
guard = TensalisClient(
    api_key="YOUR_API_KEY",
    mode="balanced"  # Use "strict" for healthcare/legal
)


def safe_rag_query(
    query: str,
    llm,  # Your LangChain LLM
    vector_db,  # Your vector store
    k: int = 3,
    auto_retry: bool = True
) -> dict:
    """
    Execute a RAG query with Tensalis hallucination protection.
    
    Args:
        query: User's question
        llm: LangChain LLM instance
        vector_db: LangChain vector store
        k: Number of documents to retrieve
        auto_retry: Whether to regenerate on hallucination
    
    Returns:
        Dict with response, verification status, and sources
    """
    # Step 1: Retrieve relevant documents
    docs = vector_db.similarity_search(query, k=k)
    context = [doc.page_content for doc in docs]
    
    # Step 2: Generate response
    prompt = f"""Based on the following context, answer the question.

Context:
{chr(10).join(context)}

Question: {query}

Answer:"""
    
    response = llm(prompt)
    
    # Step 3: Verify with Tensalis
    try:
        result = guard.verify(
            response=response,
            context=context,
            metadata={"query": query, "k": k}
        )
    except TensalisAPIError as e:
        # Log error but don't block the response
        print(f"Tensalis API error: {e}")
        return {
            "response": response,
            "verified": None,
            "sources": docs,
            "error": str(e)
        }
    
    # Step 4: Handle result
    if result.is_blocked:
        if auto_retry:
            # Retry with more explicit grounding
            strict_prompt = f"""Answer ONLY using the facts below. Do not add any information.

Facts:
{chr(10).join(f"- {c}" for c in context)}

Question: {query}

Answer (use only the facts above):"""
            
            response = llm(strict_prompt)
            
            # Re-verify
            result = guard.verify(response=response, context=context)
            
            if result.is_blocked:
                return {
                    "response": "I cannot provide a verified answer to this question.",
                    "verified": False,
                    "reason": result.reason,
                    "sources": docs
                }
        else:
            return {
                "response": None,
                "verified": False,
                "reason": result.reason,
                "severity": result.severity,
                "sources": docs
            }
    
    return {
        "response": response,
        "verified": True,
        "confidence": result.confidence,
        "latency_ms": result.latency_ms,
        "sources": docs
    }


# Example usage with LangChain components
if __name__ == "__main__":
    # This is a demonstration - replace with your actual LangChain setup
    
    # Mock LLM for demonstration
    class MockLLM:
        def __call__(self, prompt: str) -> str:
            return "Returns are accepted within 90 days of purchase."
    
    # Mock vector store
    class MockDoc:
        def __init__(self, content):
            self.page_content = content
    
    class MockVectorDB:
        def similarity_search(self, query: str, k: int) -> List:
            return [
                MockDoc("Returns are accepted within 30 days of purchase."),
                MockDoc("All returns require original receipt."),
            ]
    
    # Run example
    result = safe_rag_query(
        query="What is the return policy?",
        llm=MockLLM(),
        vector_db=MockVectorDB(),
        auto_retry=True
    )
    
    print(f"Response: {result['response']}")
    print(f"Verified: {result['verified']}")
    if not result['verified']:
        print(f"Reason: {result.get('reason', 'N/A')}")
