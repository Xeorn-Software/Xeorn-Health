import pytest
from bs4 import BeautifulSoup
import re

def test_html_structure(client):
    """Test that the HTML structure is correct."""
    # Get the main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check page title
    assert 'RWANA Health Voice Assistant' in soup.title.string
    
    # Verify main sections exist
    assert soup.select('#health-tab-pane')
    assert soup.select('#mental-tab-pane')
    assert soup.select('#breathing-tab-pane')
    assert soup.select('#appointment-tab-pane')
    assert soup.select('#health-tracking-tab-pane')

def test_form_submission_elements(client):
    """Test that the form submission elements are present."""
    # Get the main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check that the text form exists
    text_form = soup.find(id='textForm')
    assert text_form is not None
    
    # Check that the text input exists
    text_input = soup.find(id='textInput')
    assert text_input is not None
    assert text_input.get('placeholder')
    
    # Check that the submit button exists
    submit_button = text_form.find('button', type='submit')
    assert submit_button is not None
    
    # Check that the voice recording button exists
    record_button = soup.find(id='recordButton')
    assert record_button is not None
    
    # Check that the language selector exists
    language_select = soup.find(id='languageSelect')
    assert language_select is not None
    assert language_select.find('option', value='rw-RW')
    assert language_select.find('option', value='en-US')

def test_javascript_includes(client):
    """Test that all required JavaScript files are included."""
    # Get the main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for Bootstrap
    bootstrap_script = soup.find('script', src=lambda s: s and 'bootstrap' in s.lower())
    assert bootstrap_script is not None
    
    # Check for RecordRTC
    recordrtc_script = soup.find('script', src=lambda s: s and 'recordrtc' in s.lower())
    assert recordrtc_script is not None
    
    # Check for Chart.js
    chartjs_script = soup.find('script', src=lambda s: s and 'chart.js' in s.lower())
    assert chartjs_script is not None
    
    # Check for service worker registration code
    service_worker_script = soup.find(string=lambda s: s and 'serviceWorker' in s)
    assert service_worker_script is not None

def test_javascript_event_handlers(client):
    """Test that the required JavaScript event handlers are defined."""
    # Get the main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Get the JavaScript code as a string
    script_content = str(response.data)
    
    # Check for key event handlers
    assert 'addEventListener(\'submit\'' in script_content
    assert 'getElementById(\'recordButton\').addEventListener(\'click\'' in script_content
    assert 'getElementById(\'clearChat\').addEventListener(\'click\'' in script_content
    assert 'getElementById(\'startBreathingBtn\').addEventListener(\'click\'' in script_content
    assert 'getElementById(\'appointmentForm\').addEventListener(\'submit\'' in script_content
    
    # Check for key API calls
    assert 'fetch(\'/process_text\'' in script_content
    assert 'fetch(\'/process_audio\'' in script_content
    assert 'fetch(\'/send_sms\'' in script_content
    assert 'fetch(\'/breathing_exercise' in script_content
    assert 'fetch(\'/add_appointment\'' in script_content
    assert 'fetch(\'/get_appointments\'' in script_content
    assert 'fetch(\'/health_tracking\'' in script_content

def test_responsive_design(client):
    """Test that the page has responsive design elements."""
    # Get the main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for responsive viewport meta tag
    viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
    assert viewport_meta is not None
    assert 'width=device-width' in viewport_meta.get('content', '')
    
    # Check for Bootstrap responsive grid classes
    assert soup.find(class_=lambda c: c and 'col-md-' in c)
    assert soup.find(class_=lambda c: c and 'row' in c)
    
    # Check for responsive form elements
    assert soup.find(class_=lambda c: c and 'form-control' in c)
    
    # Check for responsive buttons
    assert soup.find(class_=lambda c: c and 'btn' in c)
