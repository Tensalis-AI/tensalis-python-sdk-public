# examples/streaming_verification.py
"""
Example: Real-time verification of streaming LLM responses.

This example demonstrates how to verify responses as they stream,
enabling early termination when hallucinations are detected.
"""

from tensalis import TensalisClient
from typing import Iterator


def mock_streaming_llm(prompt: str) -> Iterator[str]:
    """
    Mock streaming LLM for demonstration.
    Replace with your actual streaming LLM (OpenAI, Anthropic, etc.)
    """
    # Simulates streaming response
    response = "The refund policy allows returns within 90 days. Original receipt is required. Items must be unused."
    
    for word in response.split():
        yield word + " "


def stream_with_verification(
    prompt: str,
    context: list,
    llm_stream_fn,
    client: TensalisClient,
    on_block: callable = None
) -> str:
    """
    Stream LLM response with real-time verification.
    
    Args:
        prompt: The prompt to send to the LLM
        context: Source documents for verification
        llm_stream_fn: Function that returns streaming iterator
        client: TensalisClient instance
        on_block: Callback when hallucination detected
    
    Returns:
        The (possibly truncated) response
    """
    response_stream = llm_stream_fn(prompt)
    accumulated = []
    
    for chunk in client.verify_stream(
        response_stream=response_stream,
        context=context,
        check_interval=25  # Check every ~25 tokens
    ):
        if chunk["status"] == "BLOCKED":
            if on_block:
                on_block(chunk["result"])
            
            # Return what we have so far + warning
            return "".join(accumulated) + "\n\n[Response truncated: verification failed]"
        
        accumulated.append(chunk["text"])
        print(chunk["text"], end="", flush=True)  # Real-time output
    
    print()  # Newline after streaming
    return "".join(accumulated)


def handle_block(result: dict):
    """Handle hallucination detection."""
    print(f"\n\n⚠️  Hallucination detected!")
    print(f"   Severity: {result.get('severity', 'UNKNOWN')}")
    print(f"   Reason: {result.get('reason', 'N/A')}")
    print(f"   Layer: {result.get('layer', 'N/A')}")


if __name__ == "__main__":
    # Initialize client
    client = TensalisClient(
        api_key="YOUR_API_KEY",
        mode="balanced"
    )
    
    # Source context
    context = [
        "Returns are accepted within 30 days of purchase.",
        "Original receipt is required for all returns.",
        "Items must be in original, unopened packaging."
    ]
    
    print("Starting streaming verification...\n")
    print("-" * 50)
    
    # Stream with verification
    final_response = stream_with_verification(
        prompt="What is the refund policy?",
        context=context,
        llm_stream_fn=mock_streaming_llm,
        client=client,
        on_block=handle_block
    )
    
    print("-" * 50)
    print(f"\nFinal response:\n{final_response}")
