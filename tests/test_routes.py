import pytest
import json
from unittest.mock import patch, MagicMock
from io import BytesIO
from datetime import datetime, timedelta

def test_index_route(client):
    """Test the main index route."""
    # Call the route
    response = client.get('/')
    
    # Check that the response is valid
    assert response.status_code == 200
    # Check that the HTML contains expected content
    assert b'RWANA Health Voice Assistant' in response.data
    assert b'Rural and Urban Wellness Network Assistant' in response.data

@patch('app.process_text_input')
def test_handle_text_route(mock_process_text, client):
    """Test the text processing route."""
    # Setup the mock to return a predefined response
    mock_process_text.return_value = "Mock response for health question"
    
    # Make a POST request with form data
    response = client.post('/process_text', data={
        'text_input': 'Test question',
        'mode': 'health'
    })
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the correct data was returned
    assert data['success'] is True
    assert data['response'] == "Mock response for health question"
    
    # Verify the process_text_input function was called with correct args
    mock_process_text.assert_called_once_with('Test question', 'health')

def test_handle_text_route_empty_input(client):
    """Test the text processing route with empty input."""
    # Make a POST request with empty form data
    response = client.post('/process_text', data={
        'text_input': '',
        'mode': 'health'
    })
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify error is returned
    assert 'error' in data
    assert "No text input provided" in data['error']

@patch('app.process_audio_input')
def test_handle_audio_route(mock_process_audio, client):
    """Test the audio processing route."""
    # Setup the mock to return a predefined response
    mock_process_audio.return_value = "Mock response for audio input"
    
    # Create a test audio file
    data = b'test audio data'
    audio_file = (BytesIO(data), 'test.wav')
    
    # Make a POST request with the audio file
    response = client.post('/process_audio', 
                          data={'audio': audio_file}, 
                          content_type='multipart/form-data')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the correct data was returned
    assert data['success'] is True
    assert data['response'] == "Mock response for audio input"
    
    # Verify the process_audio_input function was called
    mock_process_audio.assert_called_once()

def test_handle_audio_route_no_file(client):
    """Test the audio processing route with no file."""
    # Make a POST request without a file
    response = client.post('/process_audio')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify error is returned
    assert 'error' in data
    assert "No audio file provided" in data['error']

@patch('app.send_sms_notification')
def test_handle_sms_route(mock_send_sms, client):
    """Test the SMS notification route."""
    # Setup the mock to return a success response
    mock_send_sms.return_value = {"success": True, "message": "SMS sent successfully"}
    
    # Make a POST request with JSON data
    response = client.post('/send_sms', 
                         json={
                             'doctor_number': '+250700000000',
                             'case_summary': 'Test case summary'
                         })
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the correct data was returned
    assert data['success'] is True
    assert "SMS sent successfully" in data['message']
    
    # Verify the send_sms_notification function was called with correct args
    mock_send_sms.assert_called_once_with('+250700000000', 'Test case summary')

def test_get_history_route(client, mock_session):
    """Test the chat history retrieval route."""
    # Setup mock session data
    mock_session['chat_history'] = [
        {'user': 'Test question', 'assistant': 'Test answer', 'timestamp': datetime.now().isoformat()}
    ]
    
    # Make a GET request
    response = client.get('/get_history')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the history was returned
    assert 'history' in data
    assert len(data['history']) == 1
    assert data['history'][0]['user'] == 'Test question'
    assert data['history'][0]['assistant'] == 'Test answer'

def test_breathing_exercise_route(client):
    """Test the breathing exercise route."""
    # Make a GET request
    response = client.get('/breathing_exercise?type=box')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify response structure
    assert 'name' in data
    assert 'steps' in data
    assert 'description' in data
    assert data['name'] == 'Box Breathing'
    assert len(data['steps']) == 4

@patch('app.datetime')
def test_add_appointment_route(mock_datetime, client, mock_session):
    """Test the appointment creation route."""
    # Setup mock current time
    mock_now = datetime(2025, 4, 12, 13, 0, 0)
    mock_datetime.now.return_value = mock_now
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    # Make a POST request with appointment data
    response = client.post('/add_appointment', 
                         json={
                             'date': '2025-05-01T10:00:00',
                             'specialty': 'Internal Medicine'
                         })
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the correct data was returned
    assert data['success'] is True
    assert 'appointment' in data
    assert data['appointment']['specialty'] == 'Internal Medicine'
    assert data['appointment']['date'] == '2025-05-01T10:00:00'
    
    # Verify the appointment was added to the session
    assert len(mock_session['user_data']['appointments']) == 1
    assert mock_session['user_data']['appointments'][0]['specialty'] == 'Internal Medicine'

def test_get_appointments_route(client, mock_session):
    """Test the appointments retrieval route."""
    # Setup mock appointment data
    mock_session['user_data']['appointments'] = [
        {
            'id': 'test-appointment-id',
            'date': '2025-05-01T10:00:00',
            'specialty': 'Internal Medicine',
            'status': 'scheduled',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    # Make a GET request
    response = client.get('/get_appointments')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the appointments were returned
    assert 'appointments' in data
    assert len(data['appointments']) == 1
    assert data['appointments'][0]['specialty'] == 'Internal Medicine'
    assert data['appointments'][0]['status'] == 'scheduled'

def test_health_tracking_get_route(client):
    """Test the health tracking GET route."""
    # Make a GET request
    response = client.get('/health_tracking')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify mock data is returned (when no real data exists)
    assert 'temperature' in data
    assert 'pulse' in data
    assert 'stress' in data
    assert len(data['temperature']) == 7
    assert len(data['pulse']) == 7
    assert len(data['stress']) == 7

@patch('app.datetime')
def test_health_tracking_post_route(mock_datetime, client, mock_session):
    """Test the health tracking POST route."""
    # Setup mock current time
    mock_now = datetime(2025, 4, 12, 13, 0, 0)
    mock_datetime.now.return_value = mock_now
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    # Make a POST request with health metric data
    response = client.post('/health_tracking', 
                         json={
                             'metric': 'temperature',
                             'value': 36.8
                         })
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the correct data was returned
    assert data['success'] is True
    
    # Verify the metric was added to the session
    assert 'health_metrics' in mock_session['user_data']
    assert 'temperature' in mock_session['user_data']['health_metrics']
    assert len(mock_session['user_data']['health_metrics']['temperature']) == 1
    assert mock_session['user_data']['health_metrics']['temperature'][0]['value'] == 36.8
