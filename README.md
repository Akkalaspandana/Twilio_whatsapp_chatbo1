# Setup Instructions

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd your-project
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Database Setup

### Install PostgreSQL

* **Windows**: Download from [PostgreSQL Official Site](https://www.postgresql.org/download/)

### Create Database & User

```sql
CREATE DATABASE your_database_name;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;
```

## 4. Environment Configuration

Create a `.env` file in your project root and add:

```env
FLASK_ENV=development
PORT=8080
SECRET_KEY=your_secret_key_here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

GOOGLE_CALENDAR_ID=your_calendar_id@gmail.com
GEMINI_API_KEY=your-gemini-api-key-here
```

Place your `credentials.json` (Google Calendar OAuth file) in the project root.

## 5. Run Flask App

```bash
python app.py
```

The app will be available at: [http://localhost:8080](http://localhost:8080)

## 6. Expose Localhost to Twilio

```bash
npm install -g ngrok
ngrok http 8080
```

Copy the HTTPS URL provided and set it as your Twilio WhatsApp webhook: `https://<ngrok-id>.ngrok.io/webhook` (method: POST).

## 7. Run Streamlit Dashboard (Optional)

```bash
streamlit run streamlit_dashboard.py
```

Access it at: [http://localhost:8501](http://localhost:8501)
