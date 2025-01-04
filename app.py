import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from threading import Thread
from transformers import pipeline
import speech_recognition as sr
import sqlite3
import json
import re
from rapidfuzz import fuzz, process

# Step 1: Environment and Dependencies Setup
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

# Flask app initialization
app = Flask(__name__)
socketio = SocketIO(app)

# NLP Pipelines
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
tone_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

# Global Variables
is_listening = False
greeting_message = "Hello! How can I assist you today? Please mention a product name to start."
results = []

# Step 2: Utility Functions


def fetch_product_by_name(product_name):
    try:
        # Connect to the database and fetch all product names
        connection = sqlite3.connect("crm.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM products")
        product_names = [row[0] for row in cursor.fetchall()]
        connection.close()

        # Perform fuzzy matching to find the closest product name
        match = process.extractOne(product_name, product_names, scorer=fuzz.partial_ratio)

        # Check if the match is above a threshold (e.g., 70% similarity)
        if match and match[1] > 70:
            matched_product_name = match[0]
            
            # Fetch the complete product details for the matched product name
            connection = sqlite3.connect("crm.db")
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM products WHERE name = ?", (matched_product_name,))
            product = cursor.fetchone()
            connection.close()
            
            print(f"Fuzzy match found: {matched_product_name} with confidence {match[1]}")
            return product
        else:
            print(f"No close match found for: {product_name}")
            return None
    except Exception as e:
        print(f"Error during fuzzy product matching: {e}")
        return None


def extract_product_name(text):
    try:
        # Extract entities using NER
        entities = ner_pipeline(text)
        for entity in entities:
            if "product" in entity["entity"].lower():
                product_name = entity["word"]
                
                # Validate product name against the database
                product = fetch_product_by_name(product_name)
                if product:
                    return product[1]  # Return the validated product name
        
        # Fallback: Keyword matching for predefined products
        predefined_products = ["laptop", "phone", "tablet", "camera", "Headphones", "Speaker", "Keyboard", "Mouse"]
        for product_name in predefined_products:
            if product_name in text.lower():
                product = fetch_product_by_name(product_name)
                if product:
                    return product[1]
        
    except Exception as e:
        print(f"Error in extracting product name: {e}")
    
    return None

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

# Calculate the best price
def calculate_best_price(sentiment, tone, start_price, price_limit):
    sentiment_value = {"positive": 0.7, "neutral": 0.5, "negative": 0.3}
    tone_value = {
        "happy": 0.8,
        "excited": 0.9,
        "relaxed": 0.6,
        "angry": 0.3,
        "sad": 0.4,
        "bored": 0.2,
    }

    sentiment_score = sentiment_value.get(sentiment.lower(), 0.5)
    tone_score = tone_value.get(tone.lower(), 0.5)

    # Combine scores to calculate a weighted price
    weight = (sentiment_score + tone_score) / 2
    best_price = start_price + (price_limit - start_price) * weight

    # Ensure the best price is within the specified range
    best_price = max(min(best_price, start_price), price_limit)
    return best_price

def save_to_google_sheets(text, sentiment, tone, product, best_price, response):
    try:
        # Ensure all values are converted to string for compatibility with Google Sheets
        data = [str(text), str(sentiment), str(tone), str(product), str(best_price), str(response)]
        sheet.append_row(data)
        print(f"Saved to Google Sheets: {data}")
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")


# Step 3: Core Functions

# Transcribe and analyze user audio input
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

                 # Default values for variables
                sentiment, tone, best_price = "UNKNOWN", "UNKNOWN", 0.0

                # Extract product name
                product_name = extract_product_name(text)
                if product_name:
                    product = fetch_product_by_name(product_name)
                else:
                    product = None
                

                # If product found, analyze and calculate the best price
                if product:
                    try:
                        start_price = float(product[3])
                        price_limit = float(product[4])
                        sentiment = analyze_sentiment(text)
                        tone = analyze_tone(text)

                        if sentiment == "NEGATIVE" and tone == "sadness":
                            additional_discount = 0.1  # Extra 10% discount
                            adjusted_price = best_price - (best_price * additional_discount)
                            best_price = max(adjusted_price, price_limit)  # Ensure it doesn't go below the price limit
                            
                        else:
                            best_price = calculate_best_price(sentiment, tone, start_price, price_limit)
                            
                        response = (
                            f"The product '{product[1]}' is available. Based on your sentiment ({sentiment}) "
                            f"and tone ({tone}), the best price is ${best_price:.2f}."
                         
                        )
                    except ValueError as ve:
                        response = "There was an error with the price data. Please check the database."
                        print(f"Error converting price to float: {ve}")
 
                else:
                    # Default response when no product is identified
                    response = f"I couldn't identify any product related to '{text}'. Please mention a product name."

                
                results.append(
                    {
                        "text": text,
                        "sentiment": sentiment,
                        "tone": tone,
                        "product_name": product[1] if product else "None",
                        "best_price": round(best_price, 2) if best_price else "N/A",
                        "response": response,
                    }
                )
                print(response)
                # Save to Google Sheets and append results
                save_to_google_sheets(text, sentiment, tone, product, best_price, response)
            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start.")
            except Exception as e:
                print(f"Error during transcription: {e}")

# Step 4: Flask Routes

@app.route("/", methods=["GET", "POST"])
def index():
    global is_listening
    if request.method == "POST":
        if "start" in request.form:
            if not is_listening:
                is_listening = True
                Thread(target=transcribe_audio).start()
                return render_template("index.html", results=results, status="Listening started", greeting=greeting_message)
            return render_template("index.html", results=results, status="Already listening", greeting=greeting_message)
        elif "stop" in request.form:
            is_listening = False
            return render_template("index.html", results=results, status="Listening stopped")

    return render_template("index.html", results=results, status=None)

# Run Flask app
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)