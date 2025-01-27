import streamlit as st
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from transformers import pipeline
from state import Sinteraction_history
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

@st.cache_resource
def initialize_groq_model(api_key):
    try:
        return ChatGroq(model="llama3-8b-8192", api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Groq model: {e}")
        return None

os.environ["HUGGINGFACE_API_KEY"] = os.getenv("HUGGINGFACE_API_KEY")

llm = initialize_groq_model(api_key=os.environ["GROQ_API_KEY"])
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
tone_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")



# Analyze Sentiment and display in sidebar
def analyze_sentiment(text):
    """
    Analyzes the sentiment of the given text and updates the sidebar with a line chart.
    """
    try:
        # Perform sentiment analysis
        result = sentiment_analyzer(text)[0]
        sentiment_label = result["label"]
        
        # Update the interaction history and plot in the sidebar
        Sinteraction_history.loc[len(Sinteraction_history)] = {"Step": len(Sinteraction_history) + 1, "Sentiment": sentiment_label}
        # Log and return sentiment
        print(f"Sentiment Analysis Result: {result}")
        return sentiment_label
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return "UNKNOWN"


# Analyze Tone and display in sidebar
def analyze_tone(text):
    """
    Analyzes the tone of the given text and updates the sidebar with a line chart.
    """
    try:
        # Perform tone analysis
        result = tone_analyzer(text)[0]
        tone_label = result["label"]
        
        # Update the interaction history and plot in the sidebar
        Sinteraction_history.loc[len(Sinteraction_history)] = {"Step": len(Sinteraction_history) + 1, "Tone": tone_label}
        
        # Log and return tone
        print(f"Tone Analysis Result: {result}")
        return tone_label
    except Exception as e:
        print(f"Error in tone analysis: {e}")
        return "UNKNOWN"
