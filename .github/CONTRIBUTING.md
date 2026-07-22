# Contributing to Crosswire

Thank you for your interest in contributing to Crosswire!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/crosswire.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Install dependencies: `pip install -r requirements.txt`
5. Make your changes
6. Run tests: `python tests/test_basic.py`
7. Commit your changes: `git commit -m 'Add amazing feature'`
8. Push to the branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## Development Setup

```bash
# Install in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium

# Start dashboard for testing
python dashboard/app.py
```

## Adding a New Platform

1. Create `adapters/your_platform.py`
2. Implement `BaseTargetAdapter` (and optionally `BaseSourceAdapter`)
3. Add to `adapters/__init__.py`
4. Add to `adapters/engine.py` adapter map
5. Add to `config/settings.example.json`
6. Add AI transformation prompt in `adapters/ai_transformer.py`
7. Add to dashboard platform list in `dashboard/app.py`
8. Update `n8n-workflow.json` with new platform node
9. Write tests in `tests/`
10. Update `README.md` and `CHANGELOG.md`

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for public functions
- Keep functions under 50 lines
- Use meaningful variable names

## Testing

```bash
# Run basic tests
python tests/test_basic.py

# Run with pytest (optional)
pytest tests/
```

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include Python version and OS
- Include error messages/logs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
