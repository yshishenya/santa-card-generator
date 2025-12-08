"""Test package for Santa project backend services.

This package contains comprehensive unit tests for the core services:

Modules:
    conftest: Pytest fixtures for mocks, sample data, and test utilities
    test_session_manager: Tests for SessionManager session handling
    test_card_service: Tests for CardService card generation workflow
    test_gemini: Tests for GeminiClient AI integration

Test Coverage Goals:
    - Minimum 80% code coverage for core modules
    - All public methods tested
    - Both success and error paths covered
    - Edge cases and boundary conditions tested

Running Tests:
    pytest                           # Run all tests
    pytest -v                        # Verbose output
    pytest --cov=src                 # With coverage report
    pytest tests/test_card_service.py  # Run specific test file
    pytest -k "test_create_session"  # Run tests matching pattern
"""
