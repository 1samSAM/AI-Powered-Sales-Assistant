import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from threading import Thread
from transformers import pipeline
import speech_recognition as sr
import sqlite3
import json

# Step 1: Environment and Dependencies Setup
# Constants for Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = "alert-rush-445806-v2-9f9cb653e266.json"

# Google Sheets Authentication
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
client = gspread.authorize(credentials)

# Access Google Sheet
sheet = client.open("my project").sheet1

# Flask app
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize NLP Pipelines
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
tone_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
'''
# Database setup
def init_crm_database():
    connection = sqlite3.connect("crm.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            start_price REAL,
            price_limit REAL,
            availability TEXT
        )
    """)

    cursor.execute("DELETE FROM products")  # Clear existing data

    # Populate sample data
    products = [
        ("Laptop", "Electronics", 500, 450, "In Stock"),
        ("Phone", "Electronics", 300, 250, "In Stock"),
        ("Tablet", "Electronics", 200, 180, "Out of Stock"),
        ("Smartwatch", "Accessories", 150, 130, "In Stock"),
        ("Camera", "Electronics", 400, 350, "In Stock"),
        ("Headphones", "Accessories", 100, 80, "In Stock"),
        ("Speaker", "Electronics", 120, 100, "Out of Stock"),
        ("Monitor", "Electronics", 250, 200, "In Stock"),
        ("Keyboard", "Accessories", 50, 40, "In Stock"),
        ("Mouse", "Accessories", 30, 25, "In Stock")
    ]

    cursor.executemany("INSERT INTO products (name, category, start_price, price_limit, availability) VALUES (?, ?, ?, ?, ?)", products)
    connection.commit()
    connection.close()

# Assign values based on sentiment and tone
def calculate_product_value(sentiment, tone, start_price, price_limit):
    sentiment_value = {"POSITIVE": 0.8, "NEGATIVE": 0.5, "NEUTRAL": 0.6}
    tone_value = {"joy": 0.9, "anger": 0.4, "neutral": 0.7, "sadness": 0.5}

    sentiment_weight = sentiment_value.get(sentiment.upper(), 0.6)
    tone_weight = tone_value.get(tone.lower(), 0.6)

    # Calculate weighted price
    weighted_value = start_price - (start_price - price_limit) * (1 - sentiment_weight * tone_weight)
    return round(weighted_value, 2)
'''


# Global Variable for Transcription Thread Control
is_listening = False
results = []

# Feedback logic
def provide_feedback(sentiment, tone):
    feedback = f"Feedback: Sentiment is {sentiment} with tone {tone}. "
    if "negative" in sentiment.lower():
        if "angry" in tone.lower():
            feedback += "Consider calming the situation or rephrasing. Offer immediate resolution."
        elif "sad" in tone.lower():
            feedback += "Empathize with the customer and provide a reassuring response."
        elif "fearful" in tone.lower():
            feedback += "Address the concerns and reassure the customer with a detailed explanation."
        else:
            feedback += "Address the customer's concerns promptly and offer assistance."
    elif "positive" in sentiment.lower():
        if "happy" in tone.lower():
            feedback += "Buyer is engaged. Keep up the positive flow."
        elif "excited" in tone.lower():
            feedback += "Customer is thrilled. Consider suggesting additional products or upgrades."
        elif "relaxed" in tone.lower():
            feedback += "The customer is satisfied. Maintain a supportive tone."
        else:
            feedback += "Continue delivering excellent service to reinforce positive engagement."
    elif "neutral" in sentiment.lower():
        if "bored" in tone.lower():
            feedback += "Reignite the customer's interest with engaging details or promotions."
        elif "uncertain" in tone.lower():
            feedback += "Clarify any doubts and provide additional information."
        else:
            feedback += "Maintain the current approach, ensuring clarity and support."
    else:
        feedback += "No specific advice for this combination. Continue monitoring the interaction."

    print(feedback)
    return feedback


# Audio transcription
def transcribe_audio():
    global is_listening
    recognizer = sr.Recognizer()

    while is_listening:
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio_data = recognizer.listen(source, timeout=5)
                print("Recognizing...")
                text = recognizer.recognize_google(audio_data, language="en-US")
                print(f"Transcribed: {text}")

                # Analyze sentiment and tone
                sentiment = analyze_sentiment(text)
                tone = analyze_tone(text)

                # Provide feedback and store it in Google Sheets
                feedback = provide_feedback(sentiment, tone)
                save_to_google_sheets(text, sentiment, tone, feedback)
                
                 # Store result
                results.append({"text": text, "sentiment": sentiment, "tone": tone, "feedback": feedback})
                print(f"Processed: {text}, {sentiment}, {tone}, {feedback}")
            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except Exception as e:
                print(f"Error during transcription: {e}")


            except sr.UnknownValueError:
                print("Could not understand the audio.")
                feedback = "Error: Could not understand the audio."
                save_to_google_sheets("", "Error", "Error", feedback)
            except sr.RequestError as e:
                print(f"Request error: {e}")
                feedback = f"Error: {e}"
                save_to_google_sheets("", "Error", "Error", feedback)
            except Exception as e:
                print(f"An error occurred: {e}")
                feedback = f"Error: {e}"
                save_to_google_sheets("", "Error", "Error", feedback)


# Sentiment analysis
def analyze_sentiment(text):
    try:
        result = sentiment_analyzer(text)[0]
        return result["label"]
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return "UNKNOWN"


# Tone analysis
def analyze_tone(text):
    try:
        result = tone_analyzer(text)[0]
        return result["label"]
    except Exception as e:
        print(f"Error in tone analysis: {e}")
        return "UNKNOWN"


# Save to Google Sheets
def save_to_google_sheets(text, sentiment, tone, feedback):
    try:
        sheet.append_row([text, sentiment, tone, feedback])
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")

'''# Fetch products from CRM database
def fetch_products():
    connection = sqlite3.connect("crm.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    connection.close()
    return products
'''
# Flask Routes
@app.route("/", methods=["GET", "POST"])
def index():
    global is_listening
    if request.method == "POST":
        if "start" in request.form:
            if not is_listening:
                is_listening = True
                Thread(target=transcribe_audio).start()
                return render_template("index.html", results=results, status="Listening started")
            return render_template("index.html", results=results, status="Already listening")
        elif "stop" in request.form:
            is_listening = False
            return render_template("index.html", results=results, status="Listening stopped")

    return render_template("index.html", results=results, status=None)
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
