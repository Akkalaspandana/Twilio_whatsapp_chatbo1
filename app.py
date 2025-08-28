from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2
import PyPDF2
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import datetime
import google.generativeai as genai

app = Flask(__name__)
DB_CONFIG = {
    'host': 'localhost',
    'database': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'port': '5432'
}
pdf_text = ""
pdf_chunks = []
pdf_embeddings = None
model = None
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'  

GEMINI_API_KEY = "your_api_keys" 
genai.configure(api_key=GEMINI_API_KEY)

def extract_pdf_text(pdf_path):
    global pdf_text
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            pdf_text = text
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

def initialize_pdf_processing():
    """Initialize PDF processing and embeddings"""
    global pdf_chunks, pdf_embeddings, model
    
    pdf_path = "invock.pdf"
    if not os.path.exists(pdf_path):
        print(f"PDF file {pdf_path} not found!")
        return False
    
    text = extract_pdf_text(pdf_path)
    if not text:
        print("Failed to extract text from PDF")
        return False
    
    pdf_chunks = chunk_text(text)


    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        pdf_embeddings = model.encode(pdf_chunks)
        print(f"Successfully processed PDF with {len(pdf_chunks)} chunks")
        return True
    except Exception as e:
        print(f"Error initializing model: {e}")
        return False

def cosine_similarity(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot_product / (norm_a * norm_b)

def find_relevant_chunks(question, top_k=5):
    global model, pdf_chunks, pdf_embeddings
    
    if model is None or pdf_embeddings is None:
        return []
    
    try:
        question_embedding = model.encode([question])[0]
        
        similarities = []
        for chunk_embedding in pdf_embeddings:
            sim = cosine_similarity(question_embedding, chunk_embedding)
            similarities.append(sim)
        
        similarities = np.array(similarities)
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        relevant_chunks = []
        for idx in top_indices:
            if similarities[idx] > 0.2:  # Lower threshold for more context
                relevant_chunks.append({
                    'text': pdf_chunks[idx],
                    'similarity': similarities[idx]
                })
        
        if not relevant_chunks and len(pdf_chunks) > 0:
            for idx in top_indices[:2]:
                relevant_chunks.append({
                    'text': pdf_chunks[idx],
                    'similarity': similarities[idx]
                })
        
        return relevant_chunks
    except Exception as e:
        print(f"Error finding relevant chunks: {e}")
        return []

def generate_answer(question, relevant_chunks):
    if not relevant_chunks:
        return "I'm sorry, I couldn't find relevant information in the PDF to answer your question."
    
    try:
        context = " ".join([chunk['text'] for chunk in relevant_chunks])
        
        prompt = f"""
        You are an AI assistant that answers questions based on PDF content. Please answer the following question using ONLY the information provided in the context below.

        Question: {question}

        PDF Context:
        {context}

        Instructions:
        1. Answer the question clearly and concisely
        2. Use only information from the provided context
        3. If the context doesn't contain enough information, say "I don't have enough information from the PDF to answer this question completely"
        4. Provide specific details and examples from the context when possible
        5. Keep your answer focused and relevant to the question
        6. If the question is about features, benefits, or capabilities, highlight the key points from the context

        Answer:
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        answer = response.text.strip()
        
        if len(answer) > 500:
            sentences = answer.split('. ')
            truncated_answer = '. '.join(sentences[:3]) + '.'
            return truncated_answer
        
        return answer
        
    except Exception as e:
        print(f"Error generating answer with Gemini: {e}")
        # Fallback to smart answer generation
        return generate_smart_fallback_answer(question, relevant_chunks)

def generate_smart_fallback_answer(question, relevant_chunks):
    if not relevant_chunks:
        return "I'm sorry, I couldn't find relevant information in the PDF to answer your question."
    
    context = " ".join([chunk['text'] for chunk in relevant_chunks])
    
    context = re.sub(r'\s+', ' ', context).strip()
    
    question_lower = question.lower()
    
    if 'what is' in question_lower or 'what are' in question_lower:
        sentences = re.split(r'[.!?]+', context)
        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in ['is', 'are', 'provides', 'offers', 'includes', 'features']):
                relevant_sentences.append(sentence)
        
        if relevant_sentences:
            cleaned_sentences = []
            for sentence in relevant_sentences[:2]:
                # Remove emojis and extra formatting
                cleaned = re.sub(r'[📦🚀🛠●✔📞👉]', '', sentence)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned and len(cleaned) > 10:
                    cleaned_sentences.append(cleaned)
            
            if cleaned_sentences:
                return "Based on the PDF: " + ". ".join(cleaned_sentences) + "."
    
    if any(word in question_lower for word in ['feature', 'capability', 'function', 'tool']):
        sentences = re.split(r'[.!?]+', context)
        feature_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and any(word in sentence.lower() for word in ['feature', 'capability', 'function', 'tool', 'management', 'tracking', 'automation']):
                feature_sentences.append(sentence)
        
        if feature_sentences:
            cleaned_features = []
            for sentence in feature_sentences[:3]:
                cleaned = re.sub(r'[📦🚀🛠●✔📞👉]', '', sentence)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned and len(cleaned) > 10:
                    cleaned_features.append(cleaned)
            
            if cleaned_features:
                return "Key features mentioned in the PDF: " + ". ".join(cleaned_features) + "."
    
    if any(word in question_lower for word in ['benefit', 'advantage', 'help', 'improve']):
        sentences = re.split(r'[.!?]+', context)
        benefit_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and any(word in sentence.lower() for word in ['help', 'improve', 'benefit', 'advantage', 'efficiency', 'productivity']):
                benefit_sentences.append(sentence)
        
        if benefit_sentences:
            cleaned_benefits = []
            for sentence in benefit_sentences[:2]:
                cleaned = re.sub(r'[📦🚀🛠●✔📞👉]', '', sentence)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned and len(cleaned) > 10:
                    cleaned_benefits.append(cleaned)
            
            if cleaned_benefits:
                return "Benefits according to the PDF: " + ". ".join(cleaned_benefits) + "."
    
    sentences = re.split(r'[.!?]+', context)
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if meaningful_sentences:
        cleaned_sentences = []
        for sentence in meaningful_sentences[:2]:
            cleaned = re.sub(r'[📦🚀🛠●✔📞👉]', '', sentence)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned and len(cleaned) > 10:
                cleaned_sentences.append(cleaned)
        
        if cleaned_sentences:
            return "Based on the PDF content: " + ". ".join(cleaned_sentences) + "."
    
    cleaned_context = re.sub(r'[📦🚀🛠●✔📞👉]', '', context)
    cleaned_context = re.sub(r'\s+', ' ', cleaned_context).strip()
    return cleaned_context[:300] + "..." if len(cleaned_context) > 300 else cleaned_context

def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            business_name VARCHAR(100) NOT NULL,
            demo_date VARCHAR(50),
            demo_time VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def get_google_calendar_service():
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json file not found!")
                print("Please download your Google Calendar API credentials and save as 'credentials.json'")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building calendar service: {e}")
        return None

def parse_date_time(date_str, time_str):
    try:
        date_str = date_str.strip().lower()
        time_str = time_str.strip().lower()
        
        now = datetime.datetime.now()
        
        if 'monday' in date_str or 'mon' in date_str:
            target_date = now + datetime.timedelta(days=(0 - now.weekday()) % 7)
        elif 'tuesday' in date_str or 'tue' in date_str:
            target_date = now + datetime.timedelta(days=(1 - now.weekday()) % 7)
        elif 'wednesday' in date_str or 'wed' in date_str:
            target_date = now + datetime.timedelta(days=(2 - now.weekday()) % 7)
        elif 'thursday' in date_str or 'thu' in date_str:
            target_date = now + datetime.timedelta(days=(3 - now.weekday()) % 7)
        elif 'friday' in date_str or 'fri' in date_str:
            target_date = now + datetime.timedelta(days=(4 - now.weekday()) % 7)
        elif 'saturday' in date_str or 'sat' in date_str:
            target_date = now + datetime.timedelta(days=(5 - now.weekday()) % 7)
        elif 'sunday' in date_str or 'sun' in date_str:
            target_date = now + datetime.timedelta(days=(6 - now.weekday()) % 7)
        else:
            for fmt in ['%d %B', '%d %b', '%B %d', '%b %d', '%d/%m', '%m/%d']:
                try:
                    target_date = datetime.datetime.strptime(date_str, fmt)
                    target_date = target_date.replace(year=now.year)
                    if target_date < now:
                        target_date = target_date.replace(year=now.year + 1)
                    break
                except ValueError:
                    continue
        else:
                target_date = now + datetime.timedelta(days=1)
        
        time_str = time_str.replace('am', ' AM').replace('pm', ' PM')
        for fmt in ['%I:%M %p', '%I %p', '%H:%M', '%H']:
            try:
                time_obj = datetime.datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
        else:
            
            time_obj = datetime.time(10, 0)
        
        event_datetime = datetime.datetime.combine(target_date.date(), time_obj)
        
        return event_datetime
    except Exception as e:
        print(f"Error parsing date/time: {e}")
        return datetime.datetime.now() + datetime.timedelta(days=1, hours=10)

def create_calendar_event(name, email, business_name, demo_date, demo_time):
    try:
        service = get_google_calendar_service()
        if not service:
            return False, "Failed to authenticate with Google Calendar"
        
        event_datetime = parse_date_time(demo_date, demo_time)
        
        event = {
            'summary': f'Demo Meeting - {business_name}',
            'description': f'Demo meeting with {name} from {business_name}\nEmail: {email}\nDemo Date: {demo_date}\nDemo Time: {demo_time}',
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (event_datetime + datetime.timedelta(hours=1)).isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [
                {'email': email},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, f"Event created: {event.get('htmlLink')}"
        
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return False, f"Failed to create calendar event: {str(e)}"

def save_user_data(name, email, business_name, demo_date=None, demo_time=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO users (name, email, business_name, demo_date, demo_time)
        VALUES (%s, %s, %s, %s, %s)
    ''', (name, email, business_name, demo_date, demo_time))
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    print(f"Received message from {from_number}: {incoming_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    if not hasattr(app, 'user_sessions'):
        app.user_sessions = {}
    
    if from_number not in app.user_sessions:
        # New user - start collecting information
        print(f"New user session created for {from_number}")
        app.user_sessions[from_number] = {
            'step': 'name',
            'data': {}
        }
        msg.body("Welcome! Please provide your name:")
    
    else:
        session = app.user_sessions[from_number]
        print(f"Existing session for {from_number}, step: {session['step']}")
        
        if session['step'] == 'name':
            session['data']['name'] = incoming_msg
            session['step'] = 'email'
            msg.body("Thank you! Please provide your email address:")
            
        elif session['step'] == 'email':
            session['data']['email'] = incoming_msg
            session['step'] = 'business'
            msg.body("Great! Please provide your business name:")
            
        elif session['step'] == 'business':
            session['data']['business_name'] = incoming_msg
            session['step'] = 'demo_choice'
            msg.body("Great! Would you like to schedule a demo meeting? Please reply with 'yes', 'demo', or 'no'.")
        
        elif session['step'] == 'demo_choice':
            user_choice = incoming_msg.lower().strip()
            if user_choice in ['yes', 'demo', 'y', 'sure', 'okay']:
                session['step'] = 'demo_date'
                msg.body("Perfect! Let's schedule a demo meeting. What is your preferred date for the demo? (e.g., Monday, Tuesday, or specific date like 15th March)")
            elif user_choice in ['no', 'n', 'skip', 'not now', 'later']:
                try:
                    print("Saving user data to database (no demo)...")
                    save_user_data(
                        session['data']['name'],
                        session['data']['email'],
                        session['data']['business_name']
                    )
                    print("User data saved successfully!")
                    
                    msg.body("No problem! Your information has been saved. You can now ask me any questions about our services or the PDF content. Type 'help' for options or ask your question directly!")
                    
                    session['step'] = 'question_mode'
                    print("Session moved to question mode (skipped demo)")
                except Exception as e:
                    print(f"Error saving user data: {e}")
                    msg.body("Sorry, there was an error saving your information. Please try again.")
                    del app.user_sessions[from_number]
            else:
                msg.body("Please reply with 'yes' if you want to schedule a demo, or 'no' if you'd like to skip it for now.")
        
        elif session['step'] == 'demo_date':
            session['data']['demo_date'] = incoming_msg
            session['step'] = 'demo_time'
            msg.body("Perfect! What time would you prefer for the demo? (e.g., 10:00 AM, 2:30 PM, or any time that works for you)")
        
        elif session['step'] == 'demo_time':
            session['data']['demo_time'] = incoming_msg
            print(f"Processing demo time: {incoming_msg}")
            
            try:
                print("Saving user data to database...")
                save_user_data(
                    session['data']['name'],
                    session['data']['email'],
                    session['data']['business_name'],
                    session['data']['demo_date'],
                    session['data']['demo_time']
                )
                print("User data saved successfully!")
                
                print("Creating Google Calendar event...")
                calendar_success, calendar_message = create_calendar_event(
                    session['data']['name'],
                    session['data']['email'],
                    session['data']['business_name'],
                    session['data']['demo_date'],
                    session['data']['demo_time']
                )
                print(f"Calendar creation result: {calendar_success}, {calendar_message}")
                
                if calendar_success:
                    msg.body("Thank you! Your information and demo schedule have been saved successfully. A calendar invitation has been sent to your email. You can now ask me any questions about our services or the PDF content. Type 'help' for options or ask your question directly!")
                else:
                    msg.body("Thank you! Your information has been saved. There was an issue creating the calendar event, but we'll contact you about the demo. You can now ask me any questions about our services or the PDF content. Type 'help' for options or ask your question directly!")
                
                session['step'] = 'question_mode'
                print("Session moved to question mode")
            except Exception as e:
                print(f"Error in demo_time processing: {e}")
                msg.body("Sorry, there was an error saving your information. Please try again.")
                del app.user_sessions[from_number]
        
        elif session['step'] == 'question_mode':
            if incoming_msg.lower() in ['help', 'menu', 'options']:
                msg.body("You can ask me questions about the PDF content. Just type your question and I'll search for relevant information!")
            elif incoming_msg.lower() in ['quit', 'exit', 'bye']:
                msg.body("Thank you for using our service! Goodbye!")
                del app.user_sessions[from_number]
            elif incoming_msg.lower() in ['demo', 'schedule demo', 'book demo', 'demo meeting']:
                session['step'] = 'demo_date'
                msg.body("Great! Let's schedule a demo meeting. What is your preferred date for the demo? (e.g., Monday, Tuesday, or specific date like 15th March)")
            else:
                relevant_chunks = find_relevant_chunks(incoming_msg)
                answer = generate_answer(incoming_msg, relevant_chunks)
                msg.body(answer)
    
    print(f"Sending response: {msg.body}")
    return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'pdf_loaded': len(pdf_chunks) > 0}

if __name__ == '__main__':
    create_table()
    
    print("Initializing PDF processing...")
    if initialize_pdf_processing():
        print("PDF processing initialized successfully!")
    else:
        print("Warning: PDF processing failed to initialize!")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
