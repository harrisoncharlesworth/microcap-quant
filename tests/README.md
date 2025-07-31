# Tests

Test suite for the Microcap Quant trading system.

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_ai_only.py

# Run with coverage
python -m pytest tests/ --cov=auto_trader
```

## Test Files

- `test_ai_only.py` - AI components testing (no broker required)
- `test_config_only.py` - Configuration validation
- `test_deep_research.py` - Deep research functionality
- `test_alpaca.py` - Broker integration tests
