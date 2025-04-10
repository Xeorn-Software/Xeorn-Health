from flask import Flask, render_template, request, jsonify, session
from io import BytesIO
from bs4 import BeautifulSoup
import os
import requests
import wave
import numpy as np
from groq import Groq
import json
from datetime import datetime, timedelta
import uuid
import random  # For generating mock health data

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Configuration
SMS_TOKEN = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4Mzc2OTM5MzUsImlhdCI6MTc0Mjk5OTUzNSwiaWQiOiJ1c2VyXzAxSlE5RFdHMFlXNjFFQVlSQ0ZDVlAwSkJSIiwicmV2b2tlZF90b2tlbl9jb3VudCI6MH0.yeY0USU_ggpNrDA4nLojSheg92Qet-0Lb_CFJKyq11QzjVw_-STHEW3vMepx-XU9E-lwi84pBvdgY-voWQ6dMA'
SMS_HEADERS = {'Authorization': 'Bearer ' + SMS_TOKEN}
SMS_URL = 'https://api.pindo.io/v1/sms/'
SMS_SENDER = 'PindoTest'

# Doctor database
DOCTORS = {'Internal Medicine':'+250794290793','Surgery':'+250796196556'
          ,'Pediatrics':'+250794290793','Obstetrics and Gynecology (OB-GYN)':'+250796196556',
          'Dermatology':'+250796196556','Psychiatry':'+250796196556','Radiology':'+250794290793',
          'Pathology':'+250794290793','Pharmacy':'+250794290793','Critical Care Medicine':'+250796196556',
          'Preventive Medicine':'+250796196556','Supportive and Allied Health':'+250794290793','Anesthesiology':'+250796196556'}
# Set Groq API key
os.environ["GROQ_API_KEY"] = "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"

# Mental health prompt templates
MENTAL_HEALTH_PROMPT = """You are a compassionate mental health assistant with expertise in mindfulness, 
stress reduction, and basic cognitive behavioral therapy. The user is speaking in Kinyarwanda or English, 
and they're experiencing mental health challenges. 

Offer soothing, practical advice with these guidelines:
1. ALWAYS respond with empathy and validation
2. Suggest 1-2 simple mindfulness or breathing exercises
3. If they mention severe symptoms (self-harm, suicide), treat it as an emergency and advise them to contact mental health services
4. Keep responses concise (3-5 sentences) and easy to understand
5. When appropriate, recommend talking to a professional therapist

Here is what they said: {input_text}"""

HEALTH_ASSESSMENT_PROMPT = """You are a healthcare assistant helping rural patients in Rwanda. The patient has described their symptoms in Kinyarwanda or English.

Please analyze their symptoms and provide:
1. A brief assessment of possible conditions (mention you are not a doctor)
2. Urgency level (Low, Medium, High, Emergency)
3. Whether they should see a doctor and which specialty would be most appropriate
4. Simple self-care measures they can take immediately
5. Key questions a doctor would want to know

Keep your response clear, simple, and reassuring. Here is the patient's description: {input_text}"""

# Store conversation history using sessions
@app.before_request
def session_management():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'user_data' not in session:
        session['user_data'] = {'appointments': []}
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

def translate_text(text, target_lang):
    """Translate text using Google Translate"""
    url = f"https://translate.google.com/m?hl={target_lang}&sl=auto&tl={target_lang}&q={text}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    result = soup.find('div', class_='result-container').text
    return result

def get_llm_response(input_text, system_prompt=None):
    """Get response from Groq API"""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    if system_prompt:
        formatted_prompt = system_prompt.format(input_text=input_text)
        messages = [{
            "role": "system", 
            "content": formatted_prompt
        }, {
            "role": "user",
            "content": input_text
        }]
    else:
        # For simple text processing
        messages = [{"role": "user", "content": input_text}]
    
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile"
    )
    
    response_content = chat_completion.choices[0].message.content
    cleaned_response = clean_markdown(response_content)
    return cleaned_response

def clean_markdown(text):
    """Clean markdown formatting from text"""
    import re
    # Remove bold/italic markdown
    text = re.sub(r'\*\*|\*|__|\|_', '', text)
    # Remove code blocks and inline code
    text = re.sub(r'```[\s\S]*?```|`[^`]*`', '', text)
    # Fix spacing issues
    text = re.sub(r'\s+', ' ', text)
    # Fix numbering
    text = re.sub(r'(\d+)\.\s+', r'\1. ', text)
    return text.strip()

def process_text_input(prompt, mode="health"):
    """Process text input and return response in Kinyarwanda or English"""
    # Detect language - simplified version, can be enhanced
    is_english = detect_english(prompt)
    
    # If not English, translate to English for processing
    if not is_english:
        english_text = translate_text(prompt, 'en')
    else:
        english_text = prompt
    
    # Select the appropriate prompt based on mode
    if mode == "mental_health":
        system_prompt = MENTAL_HEALTH_PROMPT
    else:
        system_prompt = HEALTH_ASSESSMENT_PROMPT
    
    # Get response from LLM
    response = get_llm_response(english_text, system_prompt)
    
    # Translate response back if original was not English
    if not is_english:
        response = translate_text(response, 'rw')
    
    # Store in conversation history
    session['chat_history'].append({
        'user': prompt,
        'assistant': response,
        'timestamp': datetime.now().isoformat(),
        'mode': mode
    })
    
    return response

def detect_english(text):
    """Simple language detection - checks if text is likely English"""
    # This is a very simple heuristic - could be replaced with a proper language detection library
    english_words = ['the', 'is', 'and', 'of', 'to', 'in', 'that', 'have', 'it', 'for', 'not', 'on', 'with']
    text_lower = text.lower()
    english_word_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
    return english_word_count > 1 or len(text) < 10

def process_audio_input(audio_file):
    """Process audio input and return response in Kinyarwanda"""
    # Save audio to a temporary file
    audio_data = audio_file.read()
    memory_file = BytesIO(audio_data)
    
    # Speech-to-text API call
    url = "https://api.pindo.io/ai/stt/rw/public"
    data = {"lang": "rw"}
    files = {'audio': ('file.wav', memory_file, 'audio/wav')}
    
    response = requests.post(url, files=files, data=data)
    
    if response.status_code != 200:
        return "Error processing audio"
    
    response_data = response.json()
    text = response_data['data']['text']
    
    # Translate to English
    english_text = translate_text(text, 'en')
    
    # Get response from LLM with system prompt
    response = get_llm_response(english_text, system_prompt=True)
    
    # Translate back to Kinyarwanda
    kiny_response = translate_text(response, 'rw')
    return kiny_response

def send_sms_notification(doctor_number, case_summary):
    """Send SMS notification to doctor"""
    data = {
        'to': doctor_number,
        'text': f"Medical Assistance Request:\n{case_summary[:160]}",
        'sender': SMS_SENDER
    }
    
    response = requests.post(SMS_URL, json=data, headers=SMS_HEADERS)
    
    # Successful status codes (200 OK or 201 Created)
    if response.status_code in (200, 201):
        try:
            response_data = response.json()
            # Check for either success status or message ID in response
            if response_data.get('status') == 'success' or response_data.get('id'):
                return True, "SMS sent successfully"
            return True, "SMS queued for delivery"  # Assume success for 200/201
        except ValueError:
            return True, "SMS sent (API response not JSON)"  # Assume success
    else:
        try:
            error_msg = response.json().get('message', 'Unknown error')
        except ValueError:
            error_msg = response.text or 'Unknown error'
        return False, f"Failed to send SMS: {error_msg}"

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', doctors=DOCTORS)

@app.route('/process_text', methods=['POST'])
def handle_text():
    """Process text input from the form"""
    text_input = request.form.get('text_input', '')
    mode = request.form.get('mode', 'health')  # Default to health mode
    
    if not text_input:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        response = process_text_input(text_input, mode)
        return jsonify({
            "response": response,
            "history": session.get('chat_history', [])[-5:]  # Return last 5 messages
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process_audio', methods=['POST'])
def handle_audio():
    """Process audio input from the form"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({"error": "No audio file selected"}), 400
    
    try:
        response = process_audio_input(audio_file)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_sms', methods=['POST'])
def handle_sms():
    """Send SMS to doctor"""
    data = request.json
    doctor_number = data.get('doctor_number')
    case_summary = data.get('case_summary')
    
    if not doctor_number or not case_summary:
        return jsonify({"success": False, "message": "Missing required information"}), 400
    
    success, message = send_sms_notification(doctor_number, case_summary)
    return jsonify({"success": success, "message": message})

@app.route('/get_history', methods=['GET'])
def get_history():
    """Get conversation history"""
    history = session.get('chat_history', [])
    return jsonify({"history": history})

@app.route('/breathing_exercise', methods=['GET'])
def breathing_exercise():
    """Get breathing exercise guidance"""
    exercise_type = request.args.get('type', 'box')
    exercises = {
        'box': {
            'name': 'Box Breathing',
            'steps': [
                {'action': 'inhale', 'duration': 4},
                {'action': 'hold', 'duration': 4},
                {'action': 'exhale', 'duration': 4},
                {'action': 'hold', 'duration': 4}
            ],
            'description': 'A technique used to calm the nervous system'
        },
        '478': {
            'name': '4-7-8 Breathing',
            'steps': [
                {'action': 'inhale', 'duration': 4},
                {'action': 'hold', 'duration': 7},
                {'action': 'exhale', 'duration': 8}
            ],
            'description': 'Helps reduce anxiety and helps people get to sleep'
        }
    }
    
    if exercise_type not in exercises:
        exercise_type = 'box'
        
    return jsonify(exercises[exercise_type])

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    """Add a new appointment"""
    data = request.json
    
    if not data or 'date' not in data or 'specialty' not in data:
        return jsonify({"success": False, "message": "Missing required information"}), 400
    
    appointment = {
        'id': str(uuid.uuid4()),
        'date': data['date'],
        'specialty': data['specialty'],
        'status': 'scheduled',
        'created_at': datetime.now().isoformat()
    }
    
    if 'user_data' not in session:
        session['user_data'] = {'appointments': []}
    
    session['user_data']['appointments'].append(appointment)
    
    return jsonify({"success": True, "appointment": appointment})

@app.route('/get_appointments', methods=['GET'])
def get_appointments():
    """Get user appointments"""
    if 'user_data' not in session:
        return jsonify({"appointments": []})
    
    return jsonify({"appointments": session['user_data'].get('appointments', [])})

@app.route('/health_tracking', methods=['GET', 'POST'])
def health_tracking():
    """Track and visualize health metrics"""
    if 'user_data' not in session:
        session['user_data'] = {'health_metrics': {}}
        
    if request.method == 'POST':
        # Get new health data from request
        data = request.json
        metric = data.get('metric')
        value = data.get('value')
        
        if not metric or value is None:
            return jsonify({"success": False, "message": "Missing metric or value"}), 400
            
        # Store in session
        if 'health_metrics' not in session['user_data']:
            session['user_data']['health_metrics'] = {}
            
        if metric not in session['user_data']['health_metrics']:
            session['user_data']['health_metrics'][metric] = []
            
        # Add timestamp with value
        session['user_data']['health_metrics'][metric].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"success": True})
    else:
        # Get data for visualization
        if 'health_metrics' not in session['user_data']:
            # Generate some mock data for first-time users
            mock_data = generate_mock_health_data()
            return jsonify(mock_data)
            
        return jsonify(session['user_data']['health_metrics'])

def generate_mock_health_data():
    """Generate some mock health data for visualization"""
    today = datetime.now()
    metrics = {
        'temperature': [],
        'pulse': [],
        'stress': []
    }
    
    # Generate 7 days of data
    for i in range(7):
        day = today - timedelta(days=6-i)
        metrics['temperature'].append({
            'value': round(random.uniform(36.5, 37.2), 1),
            'timestamp': day.isoformat()
        })
        metrics['pulse'].append({
            'value': random.randint(65, 85),
            'timestamp': day.isoformat()
        })
        metrics['stress'].append({
            'value': random.randint(1, 10),
            'timestamp': day.isoformat()
        })
    
    return metrics

if __name__ == '__main__':
    app.run(debug=True)