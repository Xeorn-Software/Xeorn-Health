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
import re

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))  # For session management

# Configuration
SMS_TOKEN = os.environ.get('SMS_TOKEN', 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4Mzc2OTM5MzUsImlhdCI6MTc0Mjk5OTUzNSwiaWQiOiJ1c2VyXzAxSlE5RFdHMFlXNjFFQVlSQ0ZDVlAwSkJSIiwicmV2b2tlZF90b2tlbl9jb3VudCI6MH0.yeY0USU_ggpNrDA4nLojSheg92Qet-0Lb_CFJKyq11QzjVw_-STHEW3vMepx-XU9E-lwi84pBvdgY-voWQ6dMA')
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
os.environ["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY", "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")

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
    
    try:
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
            model="llama3-8b-8192"
        )
        
        response_content = chat_completion.choices[0].message.content
        cleaned_response = clean_markdown(response_content)
        return cleaned_response
    except Exception as e:
        # Log the error and return a friendly message
        print(f"Error calling Groq API: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

def clean_markdown(text):
    """Clean markdown formatting from text"""
    # Remove headings (# Heading)
    text = re.sub(r'#+ +', '', text)
    
    # Remove bold/italic formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove bullet points
    text = re.sub(r'^\s*\* +', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```.*?```', lambda m: m.group(0).replace('```', ''), text, flags=re.DOTALL)
    
    # Remove inline code
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()

def process_text_input(prompt, mode="health"):
    """Process text input and return response in Kinyarwanda or English"""
    is_english = detect_english(prompt)
    
    try:
        # Choose the appropriate prompt template based on mode
        if mode == "mental_health":
            system_prompt = MENTAL_HEALTH_PROMPT
        else:  # default to health assessment
            system_prompt = HEALTH_ASSESSMENT_PROMPT
        
        # Get response from LLM
        response = get_llm_response(prompt, system_prompt)
        
        # Translate response if input was not in English
        if not is_english:
            try:
                response = translate_text(response, "rw")
            except Exception as e:
                print(f"Translation error: {str(e)}")
                # Continue with English response if translation fails
        
        # Update session history if in a Flask request context
        try:
            from flask import session, has_request_context
            if has_request_context() and 'chat_history' in session:
                session['chat_history'].append({
                    'user': prompt,
                    'assistant': response,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            # Just continue if we can't update the session (e.g., during testing)
            print(f"Note: Could not update session history: {str(e)}")
            
        return response
    except Exception as e:
        print(f"Error in text processing: {str(e)}")
        return "There was an error processing your request. Please try again."

def detect_english(text):
    """Simple language detection - checks if text is likely English"""
    # This is a very basic approach - English common words
    english_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 
                    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
                    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
                    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
                    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
                    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
                    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
                    'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
                    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
                    'hello', 'hi', 'how', 'are', 'you', 'feel', 'feeling', 'today', 'help', 'need'}
    
    # Clean and tokenize the text
    words = re.findall(r'\b\w+\b', text.lower())
    
    if not words:
        return True  # Default to English for empty input
    
    # Count English words
    english_count = sum(1 for word in words if word in english_words)
    
    # If more than 40% of words are recognized English words, consider it English
    return (english_count / len(words)) > 0.4

def process_audio_input(audio_file):
    """Process audio input and return response in Kinyarwanda"""
    try:
        # Save audio data to byte stream
        audio_bytes = audio_file.read()
        audio_stream = BytesIO(audio_bytes)
        
        # Analyze with audio processing (simplified for demo)
        # In a real app, we'd convert speech to text using a proper STT service
        # For this demo, we'll assume the audio contains a health question in Kinyarwanda
        
        # For demo: Since we can't actually transcribe, we'll use a placeholder response
        default_response = "Murakoze kubaza. Ndagerageza kumva ikibazo cyanyu."  # "Thank you for asking. I'm trying to understand your question."
        
        # Normally, we'd process the transcribed text here:
        # transcribed_text = speech_to_text(audio_bytes)
        # response = process_text_input(transcribed_text)
        
        # For demo, we'll return a canned response
        health_tips = [
            "Kunywa amazi menshi buri munsi ni byiza ku buzima bwawe.",  # Drinking plenty of water daily is good for your health
            "Kuruhuka bihagije ni ingenzi ku buzima bwiza.",  # Getting enough rest is essential for good health
            "Kurya imboga n'imbuto byinshi bigufasha kuguma muzima.",  # Eating plenty of vegetables and fruits helps you stay healthy
            "Gukora imyitozo ngororamubiri byiza ku buzima bwawe.",  # Regular exercise is good for your health
            "Gusuzumisha ku muganga buri gihe ni byiza.",  # Regular medical check-ups are important
        ]
        
        import random
        response = default_response + " " + random.choice(health_tips)
        
        # Add to conversation history if in a Flask request context
        try:
            from flask import session, has_request_context
            if has_request_context() and 'chat_history' in session:
                session['chat_history'].append({
                    'user': "[Audio Input]",
                    'assistant': response,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            # Just continue if we can't update the session (e.g., during testing)
            print(f"Note: Could not update session history: {str(e)}")
            
        return response
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return "Habaye ikibazo mu kumva amajwi yanyu. Mwongere mugerageze."  # There was a problem understanding your audio. Please try again.

def send_sms_notification(doctor_number, case_summary):
    """Send SMS notification to doctor"""
    try:
        # Format the message
        message = f"RWANA Health Assistant: New patient case summary: {case_summary[:100]}..."
        
        # Prepare payload for SMS API
        payload = {
            "to": doctor_number,
            "text": message,
            "sender": SMS_SENDER
        }
        
        # Send SMS via pindo.io API
        response = requests.post(
            SMS_URL,
            headers=SMS_HEADERS,
            json=payload
        )
        
        # Check response
        if response.status_code == 200:
            return {"success": True, "message": "SMS notification sent to doctor."}
        else:
            print(f"SMS API error: {response.status_code}, {response.text}")
            return {"success": False, "message": f"Failed to send SMS. Status code: {response.status_code}"}
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return {"success": False, "message": "Error sending SMS notification."}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', doctors=DOCTORS)

@app.route('/process_text', methods=['POST'])
def handle_text():
    """Process text input from the form"""
    try:
        # Get form data
        text_input = request.form.get('text_input', '').strip()
        mode = request.form.get('mode', 'health').strip()
        
        if not text_input:
            return jsonify({"error": "No text input provided"})
        
        # Process the text and get response
        response = process_text_input(text_input, mode)
        
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        print(f"Error handling text: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occurred while processing your request"
        })

@app.route('/process_audio', methods=['POST'])
def handle_audio():
    """Process audio input from the form"""
    try:
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"})
        
        file = request.files['audio']
        
        # If user does not select file, browser also
        # submit an empty file without filename
        if file.filename == '':
            return jsonify({"error": "No audio file selected"})
        
        # Process the audio and get response
        response = process_audio_input(file)
        
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        print(f"Error handling audio: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occurred while processing your audio"
        })

@app.route('/send_sms', methods=['POST'])
def handle_sms():
    """Send SMS to doctor"""
    try:
        data = request.json
        
        if not data or 'doctor_number' not in data or 'case_summary' not in data:
            return jsonify({
                "success": False,
                "message": "Missing doctor number or case summary"
            })
        
        doctor_number = data.get('doctor_number')
        case_summary = data.get('case_summary')
        
        result = send_sms_notification(doctor_number, case_summary)
        return jsonify(result)
    except Exception as e:
        print(f"Error handling SMS request: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error processing SMS request"
        })

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