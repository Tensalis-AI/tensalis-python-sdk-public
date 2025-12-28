# Contributing to Tensalis Python SDK

Thank you for your interest in contributing to the Tensalis Python SDK!

## Getting Started

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tensalis-ai/tensalis-python-sdk.git
   cd tensalis-python-sdk
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ -v --cov=tensalis --cov-report=html
```

### Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run all checks:
```bash
black tensalis tests
isort tensalis tests
flake8 tensalis tests
mypy tensalis
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.

When reporting bugs, please include:
- Python version
- SDK version
- Minimal reproduction code
- Expected vs actual behavior

## Code of Conduct

Please be respectful and constructive in all interactions.

## Questions?

Contact us at engineering@tensalis.com
