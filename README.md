## Description 
Voice-AI Healthcare Assistant for Rural and Urban Communities
What It Does
1. For Rural Communities: Imagine a farmer in a remote village who’s feeling unwell. They open the app, speak in Kinyarwanda, and describe their symptoms. The app translates their words and sends them to a doctor. The doctor reviews the symptoms and sends back advice via SMS. If it’s urgent, the doctor can even call the patient directly.
2. For Urban Communities: In the city, someone feeling stressed or anxious can talk tomental health chatbot. They might say, “Ndi numva ubwoba.” (I feel anxious). The chatbot listens, offers calming techniques like breathing exercises, and suggests mindfulness tips. If the user needs more help, it connects them to a licensed therapist for professional support.Also they can use the first method.

Why It Matters
1. For Rural Areas:
    * No More Long Journeys: People don’t have to travel hours to see a doctor.
    * Language No Longer a Barrier: They can speak in their own language and be understood.
    * Saves Time and Money: Quick advice means fewer trips and lower costs.
2. For Urban Areas:
    * Mental Health Support Anytime: People can get help without fear of judgment.
    * Early Intervention: The chatbot helps users manage stress before it becomes a bigger problem.
    * Connects to Professionals: For those who need it, the app links users to therapists.
3. For Everyone:
    * Scalable: This solution can grow to serve more regions and languages across Africa.
    * Empowering: It puts healthcare and mental health support in the hands of those who need it most.
## How It Works 
![Design_](https://github.com/user-attachments/assets/fe311263-9365-4cd3-87ef-52c9c4812d64)
## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/adamlogman/Irembo-Project.git
   cd Irembo-Project
   ```

2. Create and activate a virtual environment:
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Project Structure

```
Irembo-Project/
├── app.py
├── templates/
│       ├── index.html
├── requirements.txt
└── README.md
```

## Development

To add new features or fix bugs:

1. Create a new branch:
   ```
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```
   git add .
   git commit -m "Add your feature description"
   ```

3. Push your changes to the repository:
   ```
   git push origin feature/your-feature-name
   ```

## Testing

Run the test suite with:
```
pytest
```

## Deployment

For production deployment:

1. Set up a production server (e.g., Gunicorn, uWSGI)
2. Configure a reverse proxy (e.g., Nginx, Apache)
3. Set appropriate environment variables for production

Example with Gunicorn:
```
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
