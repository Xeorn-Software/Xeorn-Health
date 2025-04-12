import pytest
from unittest.mock import patch, MagicMock
import json
import os

from app import (
    translate_text,
    get_llm_response,
    clean_markdown,
    detect_english,
    process_text_input,
    process_audio_input,
    send_sms_notification
)

def test_clean_markdown():
    """Test that markdown formatting is properly cleaned."""
    # Test with various markdown elements
    markdown_text = "# Heading\n**Bold text**\n* List item\n```code block```"
    cleaned = clean_markdown(markdown_text)
    
    # Verify markdown elements are removed
    assert "# Heading" not in cleaned
    assert "**Bold text**" not in cleaned
    assert "Bold text" in cleaned
    assert "* List item" not in cleaned
    assert "List item" in cleaned
    assert "```code block```" not in cleaned
    assert "code block" in cleaned

def test_detect_english():
    """Test language detection function."""
    # English text
    assert detect_english("Hello, how are you feeling today?") is True
    
    # Non-English text (simulated Kinyarwanda)
    assert detect_english("Muraho, amakuru yawe?") is False
    
    # Mixed text with more English
    assert detect_english("Hello, muraho, how are you?") is True
    
    # Mixed text with less English
    assert detect_english("Muraho, hello, amakuru yawe?") is False

@patch('requests.get')
def test_translate_text(mock_get):
    """Test the translation function."""
    # Mock response with BeautifulSoup parseable content
    mock_response = MagicMock()
    mock_response.text = '<html><body><div class="result-container">Translated text</div></body></html>'
    mock_get.return_value = mock_response
    
    result = translate_text("Original text", "rw")
    
    # Verify the translation result
    assert result == "Translated text"
    
    # Verify the correct URL was called
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "translate.google.com" in args[0]
    assert "rw" in args[0]
    assert "Original text" in args[0]

@patch('app.Groq')
def test_get_llm_response(mock_groq, mock_groq_response):
    """Test the LLM response function."""
    # Setup the mock response
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_groq_response
    mock_groq.return_value = mock_client
    
    # Test with system prompt
    result = get_llm_response("Test input", "System prompt {input_text}")
    
    # Verify Groq was called with correct parameters
    mock_client.chat.completions.create.assert_called_once()
    args, kwargs = mock_client.chat.completions.create.call_args
    
    # Verify messages format
    assert len(kwargs['messages']) == 2
    assert kwargs['messages'][0]['role'] == 'system'
    assert kwargs['messages'][1]['role'] == 'user'
    assert kwargs['messages'][1]['content'] == 'Test input'
    
    # Verify we get back the expected response
    assert "Test response from Groq API" in result

@patch('app.get_llm_response')
@patch('app.translate_text')
@patch('app.detect_english')
def test_process_text_input(mock_detect_english, mock_translate, mock_get_llm, mock_session):
    """Test the text processing function."""
    # Setup mocks
    mock_detect_english.return_value = False  # Not English
    mock_translate.return_value = "Translated response"
    mock_get_llm.return_value = "API response"
    
    # Test health mode
    result = process_text_input("Muraho", "health")
    
    # Verify correct functions were called
    mock_detect_english.assert_called_with("Muraho")
    mock_get_llm.assert_called_once()
    mock_translate.assert_called_once()
    
    # Verify result
    assert result == "Translated response"
    
    # Check chat history was updated
    assert len(mock_session['chat_history']) == 1
    assert mock_session['chat_history'][0]['user'] == "Muraho"
    assert mock_session['chat_history'][0]['assistant'] == "Translated response"

@patch('requests.post')
def test_send_sms_notification(mock_post):
    """Test the SMS notification function."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # Call the function
    result = send_sms_notification("+250700000000", "Test case summary")
    
    # Verify SMS API was called correctly
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert 'pindo.io/v1/sms/' in args[0]
    assert kwargs['json']['to'] == "+250700000000"
    assert "Test case summary" in kwargs['json']['text']
    
    # Verify result
    assert result['success'] is True
    assert "SMS notification sent" in result['message']

def test_process_audio_input():
    """Test the audio processing function."""
    # Create a mock audio file
    mock_audio = MagicMock()
    mock_audio.read.return_value = b'test audio data'
    
    # Call the function
    result = process_audio_input(mock_audio)
    
    # Verify result has expected format (this is a placeholder response in our implementation)
    assert "Murakoze kubaza" in result
    assert isinstance(result, str)
    assert len(result) > 10  # Should have reasonable length
