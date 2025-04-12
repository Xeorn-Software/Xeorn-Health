import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from flask import session

# Make sure the application is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set test config
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
    })
    
    # Set mock environment variables for testing
    os.environ["GROQ_API_KEY"] = "test_groq_api_key"
    os.environ["SMS_TOKEN"] = "test_sms_token"
    
    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_groq_response():
    """Create a mock groq API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response from Groq API"
    return mock_response

@pytest.fixture
def mock_session(app):
    """Mock the Flask session for testing."""
    with app.test_request_context():
        # Initialize the session data
        session['chat_history'] = []
        session['user_data'] = {'appointments': []}
        session['session_id'] = 'test_session_id'
        yield session
