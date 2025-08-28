# WhatsApp Demo Scheduler & PDF Q&A Bot

A Flask-based WhatsApp bot that can schedule demo meetings and answer questions based on PDF content using Google's Gemini AI.

## 🚀 Features

- **WhatsApp Integration**: Connect with Twilio for WhatsApp messaging
- **User Registration**: Collect user details (name, email, business name)
- **Demo Scheduling**: Optional demo meeting scheduling with Google Calendar integration
- **PDF Q&A**: AI-powered question answering based on PDF content using Gemini API
- **Database Storage**: PostgreSQL database for user data management
- **Streamlit Dashboard**: Web dashboard to view registered users and analytics

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Twilio account with WhatsApp Business API
- Google Cloud Platform account
- Google Calendar API credentials
- Google Gemini API key

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd your-project
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup

#### Install PostgreSQL
- **Windows**: Download from [PostgreSQL Official Site](https://www.postgresql.org/download/windows/)
- **macOS**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`

#### Create Database
```sql
CREATE DATABASE your_database_name;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;
```

### 4. Environment Configuration

#### Update Database Configuration
Edit `app.py` and update the `DB_CONFIG`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'port': '5432'
}
```

#### Update Gemini API Key
Replace the API key in `app.py`:
```python
GEMINI_API_KEY = "your-gemini-api-key-here"
```

## 🔧 API Setup

### 1. Twilio Setup

1. **Create Twilio Account**
   - Sign up at [Twilio Console](https://console.twilio.com/)
   - Get your Account SID and Auth Token

2. **Enable WhatsApp Business API**
   - Go to Messaging → Try it out → Send a WhatsApp message
   - Follow the setup instructions

3. **Configure Webhook**
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook`
   - Method: POST

### 2. Google Calendar API Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable Calendar API**
   - Go to APIs & Services → Library
   - Search for "Google Calendar API" and enable it

3. **Create OAuth 2.0 Credentials**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: Desktop application
   - Download the JSON file and rename it to `credentials.json`
   - Place it in your project root directory

4. **Add Test Users**
   - In OAuth consent screen, add your email as a test user
   - This allows you to authenticate without app verification

### 3. Google Gemini API Setup

1. **Get API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key and update it in `app.py`

## 📁 Project Structure

```
your-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── your-pdf-file.pdf     # PDF file for Q&A
├── credentials.json      # Google Calendar API credentials
├── token.pickle          # Generated OAuth tokens
├── streamlit_dashboard.py # Streamlit dashboard
└── README.md             # This file
```

## 🚀 Running the Application

### 1. Start the Flask App
```bash
python app.py
```

The app will run on `http://localhost:8080`

### 2. Expose Local Server (for Twilio webhook)
```bash
# Install ngrok
npm install -g ngrok

# Expose your local server
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update your Twilio webhook URL.

### 3. Run Streamlit Dashboard (Optional)
```bash
streamlit run streamlit_dashboard.py
```

Access the dashboard at `http://localhost:8501`

## 🔄 Bot Flow

### User Registration Flow
1. **Welcome Message** → User provides name
2. **Email Collection** → User provides email
3. **Business Name** → User provides business name
4. **Demo Choice** → User chooses to schedule demo or skip
5. **Demo Scheduling** (if chosen):
   - Date selection
   - Time selection
   - Google Calendar event creation
6. **Q&A Mode** → User can ask questions about PDF content

### Demo Scheduling Options
- **User says "yes"**: Proceeds to schedule demo
- **User says "no"**: Skips demo and goes to Q&A mode
- **From Q&A mode**: User can type "demo" to start scheduling

## 🤖 Q&A Features

### Supported Question Types
- **What is/What are**: Definition and description questions
- **Features**: Capability and function questions
- **Benefits**: Advantage and improvement questions
- **General**: Any question about the PDF content

### AI Integration
- **Primary**: Google Gemini API (`gemini-1.5-flash`)
- **Fallback**: Smart text processing with semantic search
- **Context**: Relevant PDF chunks based on question similarity

## 📊 Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    business_name VARCHAR(100) NOT NULL,
    demo_date VARCHAR(50),
    demo_time VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Note**: The table will be created automatically when you run the application for the first time.

## 🔍 Testing

### Test Answer Generation
```bash
# Create a test script to verify PDF Q&A functionality
python -c "
import app
# Test with sample questions
questions = ['What is this about?', 'What are the main features?']
for q in questions:
    chunks = app.find_relevant_chunks(q)
    answer = app.generate_answer(q, chunks)
    print(f'Q: {q}\nA: {answer}\n')
"
```

This will test the PDF Q&A functionality with sample questions.

### Health Check
```bash
curl http://localhost:8080/health
```

Returns application status and PDF loading status.

## 🛡️ Security Considerations

- **API Keys**: Never commit API keys to version control
- **Database**: Use strong passwords for database access
- **OAuth**: Keep `credentials.json` and `token.pickle` secure
- **Webhook**: Use HTTPS URLs for Twilio webhooks

## 🐛 Troubleshooting

### Common Issues

1. **"credentials.json not found"**
   - Download OAuth credentials from Google Cloud Console
   - Place file in project root directory

2. **"Google hasn't verified this app"**
   - Add your email as a test user in OAuth consent screen
   - Click "Advanced" → "Go to [App Name] (unsafe)"

3. **"ModuleNotFoundError"**
   - Install missing dependencies: `pip install -r requirements.txt`

4. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `DB_CONFIG`

5. **Twilio Webhook Not Receiving Messages**
   - Ensure ngrok is running and URL is updated in Twilio
   - Check webhook URL format (must be HTTPS)

### Debug Mode
The Flask app runs in debug mode by default. Check console output for detailed error messages.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review console logs for error messages
3. Verify all API credentials are correctly configured
4. Ensure all dependencies are installed

## 📝 License

This project is for educational and demonstration purposes.

---

**Note**: Make sure to replace placeholder values (API keys, database credentials) with your actual credentials before running the application.
