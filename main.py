import streamlit as st
import sqlite3
import os
import time
import pandas as pd
import threading
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from transformers import pipeline
import speech_recognition as sr
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from utils import analyze_tone, analyze_sentiment
from dotenv import load_dotenv
from negotiation import handle_input, negotiation_assistant
from functools import partial  # Import partial to pass arguments
from state import Sinteraction_history

# Initialize recognizer
recognizer = sr.Recognizer()
# Global variable to control the listening state
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
# Function to transcribe audio
def transcribe_audio():
    while st.session_state.is_listening:
        with sr.Microphone() as source:
            st.write("Listening...")
            try:
                # Adjust for ambient noise and listen to the microphone
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.listen(source, timeout=5)
                st.write("Recognizing...")
                
                # Transcribe the audio to text
                text = recognizer.recognize_google(audio_data, language="en-US")
                st.session_state.customer_question = text  # Update session state with transcribed text
                st.write(f"Transcribed Text: {text}")
            except sr.WaitTimeoutError:
                st.warning("Listening timed out. Please speak again.")
            except sr.UnknownValueError:
                st.error("Sorry, I could not understand the audio.")
            except sr.RequestError:
                st.error("Sorry, there was an issue with the speech recognition service.")



# Load environment variables
load_dotenv(dotenv_path="config.env")

@st.cache_resource
def initialize_groq_model(api_key):
    try:
        return ChatGroq(model="llama3-8b-8192", api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Groq model: {e}")
        return None
    
# Set Hugging Face API key
os.environ["HUGGINGFACE_API_KEY"] = os.getenv("HUGGINGFACE_API_KEY")

# Initialize models
llm = initialize_groq_model(api_key=os.environ["GROQ_API_KEY"])
#sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
#tone_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")


# Paths
DB_PATH = "SalesCRM.db"
VECTOR_STORE_PATH = "vector_store_index"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = "alert.json"

# Google Sheets Authentication
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Load vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

@st.cache_resource
def load_vector_store(path, _embeddings):
    """
    Load or create a FAISS vector store.

    Args:
        path (str): The file path for the FAISS vector store.
        embeddings: The embeddings model to use for creating/loading the store.

    Returns:
        FAISS: An instance of the FAISS vector store.
    """
    try:
        if os.path.exists(path):
            print("Loading existing vector store index...")
            return FAISS.load_local(path, _embeddings, allow_dangerous_deserialization=True)
        else:
            print("No existing index found. Initializing a new vector store...")
            return FAISS.from_texts([], _embeddings)
    except Exception as e:
        raise RuntimeError(f"Failed to load or create vector store: {e}")


vector_store = load_vector_store(VECTOR_STORE_PATH, embeddings)


# Initialize the database with WAL mode
def get_db_connection():
    """
    Create a new SQLite database connection.
    Enables Write-Ahead Logging (WAL) mode for better concurrency.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode
    return conn


# to get customer details
def fetch_customer_data(customer_name):
    """
    Fetch customer details and interaction history from the database.
    Returns the data as a dictionary or None if the customer is not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.CustomerID, c.Name, c.Email, c.Phone, 
                   ih.LastDealStatus, ih.InteractionDate, ih.Notes, ih.Sentiment, ih.Tone, ih.Intention, r.RecommendedDeal
            FROM Customers c
            LEFT JOIN InteractionHistory ih ON c.CustomerID = ih.CustomerID
            LEFT JOIN Recommendations r ON c.CustomerID = r.CustomerID
            WHERE c.Name = ?
            ORDER BY ih.InteractionDate DESC, r.Date DESC
            LIMIT 1
            """,
            (customer_name,),
        )
        customer = cursor.fetchone()
        if customer:
            columns = [
                "CustomerID", "Name", "Email", "Phone", "LastDealStatus",
                "InteractionDate", "Notes", "Sentiment", "Tone", "Intention",
                "RecommendedDeal"
            ]
            return dict(zip(columns, customer))
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()


def execute_with_retry(cursor, query, params=(), retries=5, delay=1):
    for attempt in range(retries):
        try:
            cursor.execute(query, params)
            break  # Exit loop if query succeeds
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(delay)  # Wait before retrying
            else:
                raise
    else:
        raise RuntimeError("Database operation failed after multiple retries.")


# to insert new customer details
def add_customer_to_db(name, email, phone, sentiment, tone, intention, notes, recommendations):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Assign a new CustomerID by finding the current max ID
    execute_with_retry(
        cursor,
        "SELECT IFNULL(MAX(CustomerID), 0) + 1 FROM Customers"
    )
    new_customer_id = cursor.fetchone()[0]

    # Insert the new customer into the Customers table
    execute_with_retry(
        cursor,
        """
        INSERT INTO Customers (CustomerID, Name, Email, Phone)
        VALUES (?, ?, ?, ?)
        """,
        (new_customer_id, name, email, phone)
    )

    # Insert interaction data for the new customer
    execute_with_retry(
        cursor,
        """
        INSERT INTO InteractionHistory (CustomerID, LastDealStatus, InteractionDate, Notes, Sentiment, Tone, Intention)
        VALUES (?, ?, DATETIME('now'), ?, ?, ?, ?)
        """,
        (new_customer_id, "New", notes, sentiment, tone, intention)
    )

    execute_with_retry(
        cursor,
        """
        INSERT INTO Recommendations (CustomerID, RecommendedDeal, Date)
        VALUES (?, ?, datetime('now'))
        """,
        (new_customer_id, recommendations)
    )

    conn.commit()
    conn.close()



#def analyze_sentiment(text):
#    try:
#       result = sentiment_analyzer(text)[0]
#        print(result)
#        return result["label"]
#    except Exception as e:
#        print(f"Error in sentiment analysis: {e}")
#        return "UNKNOWN"
#def analyze_tone(text):
#    try:
#        result = tone_analyzer(text)[0]
#        print(result)
#        return result["label"]
#    except Exception as e:
#        print(f"Error in tone analysis: {e}")
#        return "UNKNOWN"


def analyze_intention(text):
    """
    Analyze the intention of the given text using an LLM and return a one-word summary.
    """
    # Prompt for LLM
    prompt = f"""
    You are an expert intention analyzer. 
    Analyze the intention of the following input text and provide a single-word summary that best represents the user's intention:

    Input Text: "{text}"

    Please respond with just one word.
    """
    
    try:
        # Invoke the LLM to get the response
        response = llm.invoke(prompt)
        # Extract and clean the response
        intention = response.content.strip().split("\n")[0]  # Ensures single-word output
        return intention
    except Exception as e:
        st.error(f"Error generating AI response: {e}")
        return "Unknown"


def recommend_deals(customer_data, customer_question=None):
    """
    Generate personalized car recommendations using LLM and vector store.
    """
    # Construct a dynamic query based on customer profile and query
    base_query = f"Customer is interested in second-hand cars. Their tone is {customer_data.get('Tone', 'Neutral')}, intention is {customer_data.get('Intention', 'General Inquiry')}, and sentiment is {customer_data.get('Sentiment', 'Neutral')}."
    additional_query = f" Query: {customer_question}" if customer_question else ""
    query = base_query + additional_query

    # Initialize recommendation results
    recommendations = "No recommendations available."
    detailed_results = []

    try:
        # Perform vector store similarity search
        if vector_store and len(vector_store.docstore._dict) > 0:  # FAISS-specific check
            search_results = vector_store.similarity_search(query, k=10)  # Retrieve top 5 results
            detailed_results = [result.page_content.strip() for result in search_results]

            # Combine the search results into a summary for LLM
            results_summary = "\n".join(f"{i+1}. {result}" for i, result in enumerate(detailed_results))

            # Use LLM to refine and format recommendations
            prompt = f"""
            You are an AI assistant tasked with creating personalized recommendations for a customer based on their preferences and query. 

            Customer Profile:
            - Name: {customer_data.get('Name', 'Unknown')}
            - Tone: {customer_data.get('Tone', 'Neutral')}
            - Intention: {customer_data.get('Intention', 'General Inquiry')}
            - Last Deal Status: {customer_data.get('LastDealStatus', 'None')}
            - Sentiment: {customer_data.get('Sentiment', 'Neutral')}
            - Notes: {customer_data.get('Notes', 'No notes available')}

            Customer Query: {customer_question or 'No specific query provided'}

            Search Results from Vector Store:
            {results_summary}

            Generate a short list of 2 recommended cars and show cars full details in one line and without adding unnecessary introductions or conclusions.
            """
            response = llm.invoke(prompt)
            recommendations = response.content.strip()

        else:
            recommendations = "The vector store does not contain data, fallback to generic recommendations."
    
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        recommendations = "Error occurred during recommendation generation."

    return recommendations

    
def generate_llm_response(customer_data, recommendations, customer_question):
    """Generate AI response for the sales assistant."""
    prompt = f"""
    You are a professional sales assistant. Based on the customer profile and recommendations, 
    generate a point-by-point summarize shorty of the last interaction and personal emotion(sentiment and tone) in a professional tone. 
    The summary should be concise yet detailed, focusing on key points relevant to the customer's needs and concerns. 

    Additionally, craft a set of clear, engaging, and concise instructions that the salesperson can use 
    to communicate the recommendations effectively to the customer. 
    These instructions should:
    - Highlight the customer's preferences.
    - Address their concerns.
    - Encourage further action.
    - Be phrased in a friendly and approachable manner.
    - Remain short and to the point.
    -explaining shorty why each option is suitable based on the customer's profile and query.

    Customer Profile:
    - Name: {customer_data.get('Name', 'Unknown')}
    - Last Deal Status: {customer_data.get('LastDealStatus', 'Unknown')}
    - Notes: {customer_data.get('Notes', 'No notes available')}
    - Sentiment: {customer_data.get('Sentiment', 'Neutral')}
    - Tone: {customer_data.get('Tone', 'Neutral')}
    - Intention: {customer_data.get('Intention', 'Inquiry')}
    
    Recommendations:
    {recommendations}
    
    Customer Question or Additional Information:
    {customer_question}
    
    Provide a clear, concise,summarize shortiy and actionable response for the salesperson.
    """
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        st.error(f"Error generating AI response: {e}")
        return "Unable to generate a response. Please try again."


# Function to update customer interaction in the database
def update_customer_interaction(customer_id, last_deal_status, notes, recommendations, sentiment, tone, intention):
    """
    Update the customer interaction details in the database for an existing customer.
    If the customer interaction does not exist, this will update the latest entry for the customer.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE InteractionHistory
        SET 
            LastDealStatus = ?, 
            Notes = ?, 
            Sentiment = ?, 
            Tone = ?, 
            Intention = ?, 
            InteractionDate = datetime('now')
        WHERE CustomerID = ?
        """,
        (last_deal_status, notes, sentiment, tone, intention, customer_id)
    )
    # Check if CustomerID exists in the Recommendations table
    cursor.execute(
        """
        SELECT COUNT(*) FROM Recommendations WHERE CustomerID = ?
        """,
        (customer_id,)
    )
    exists = cursor.fetchone()[0]  # Fetch the count
    if exists:
        cursor.execute(
            """
            UPDATE Recommendations
            SET
                RecommendedDeal = ?,
                Date = datetime('now') 
            WHERE CustomerID = ?      
            """,
            (recommendations, customer_id)
        )
    
    else:
        cursor.execute(
            """
            INSERT INTO Recommendations (CustomerID, RecommendedDeal, Date)
            VALUES (?, ?, datetime('now'))
            """,
            (customer_id, recommendations)
        )
    
    conn.commit()
    conn.close()


def post_call_summary(customer_data, recommendations, customer_question, llm_response):
    prompt = f"""
You are an AI assistant tasked with summarizing customer interactions concisely and effectively. 
Generate a structured summary that includes:

1. **Summary**: A concise overview of the interaction focusing on the key customer needs and your recommendations.
2. **Response Highlights**: A bulleted list of the main points in your response to the customer query.
3. **Recommendations**: A bulleted list of the cars recommended with essential details such as type, price, and condition.

Ensure that:
- The summary avoids redundant or generic sentences like introductions or conclusions.
- The summary is brief but provides all critical information for future reference.
- Incorporate the customer's previous notes, if available, for context.
- Write the shortest useful summary that can be easily referred to in future interactions.

Parameters:
        customer_data (dict): Customer's data, including previous notes and interaction history.
        recommendations (str): Recommendations generated for the customer.
        customer_question (str): The query or additional information provided by the customer.
        llm_response (str): The AI-generated response to the customer's query.

Input Data:
- Customer Data: {customer_data}
-Previous Notes: {customer_data.get('Notes', 'No notes available')}
- Customer Query: {customer_question}
- AI Response: {llm_response}
- Recommendations: {recommendations}

Generate the structured summary directly without adding unnecessary introductions or conclusions.
"""

    try:
        # Invoke the LLM to generate the summary
        response = llm.invoke(prompt)
        # Return the stripped content of the response
        return response.content.strip()
    except Exception as e:
        # Handle errors gracefully and notify the user
        st.error(f"Error generating post-call summary: {e}")
        return "Summary not available."






# Main App

def home_page():
    st.title("AI Sales Assistant")
    
    customer_name = st.text_input("Enter Customer Name:")
    # Input for customer query (text or audio)
    st.write("Enter Customer Query or Additional Information:")

    # Initialize session state for customer_question
    if "customer_question" not in st.session_state:
        st.session_state.customer_question = ""

    # Option to choose between text or audio input
    input_method = st.radio("Select Input Method:", ("Text", "Audio"))

    if input_method == "Text":
        # Text input
        customer_question = st.text_area("Type your query here:", value=st.session_state.customer_question)
        st.session_state.customer_question = customer_question
    else:
        # Audio input
        if st.button("Start Listening" if not st.session_state.is_listening else "Stop Listening"):
            st.session_state.is_listening = not st.session_state.is_listening

            # Start/stop the transcription thread
            if st.session_state.is_listening:
                threading.Thread(target=transcribe_audio, daemon=True).start()
            else:
                st.write("Listening stopped.")

        # Display the transcribed text in the text area
        customer_question = st.text_area("Transcribed Query:", value=st.session_state.customer_question)



    # Button for fetching recommendations
    if st.button("Get Recommendations"):
        if customer_name.strip():  # Check if customer name is provided
            with st.spinner("Fetching data and generating recommendations..."):
                # Check if customer exists in the database
                customer_data = fetch_customer_data(customer_name)
                
                if customer_data:
                    # Customer exists, generate recommendations and responses
                    recommendations = recommend_deals(customer_data, customer_question)
                    llm_response = generate_llm_response(customer_data, recommendations, customer_question)
                    
                    # Generate post-call summary
                    summary = post_call_summary(customer_data, recommendations, customer_question, llm_response)

                    # Update database with the post-call summary and latest interaction details
                    update_customer_interaction(
                        customer_id=customer_data['CustomerID'],
                        last_deal_status="Active",
                        notes=summary,
                        recommendations=recommendations,
                        sentiment=analyze_sentiment(customer_question),
                        tone=analyze_tone(customer_question),
                        intention=analyze_intention(customer_question),
                    )
                    
                    st.markdown(f"### Recommendations for {customer_name}:")
                    st.markdown(recommendations)
                    st.markdown(f"### Assistant Response:\n{llm_response}")
                    st.write(f"Customer '{customer_name}' successfully updated with last interaction")
                
                else:
                    # New customer: Add to the database and process the query
                    st.subheader("New Customer")
                    if customer_question.strip():  # Check if customer query is provided
                        # Analyze sentiment and tone from the customer query
                        sentiment = analyze_sentiment(customer_question)
                        tone = analyze_tone(customer_question)
                        intention = analyze_intention(customer_question)   
                        
                        # Generate recommendations and responses for the new customer
                        recommendations = recommend_deals(
                            customer_data={
                                "Name": customer_name,
                                "LastDealStatus": "New",
                                "Notes": "new customer",
                                "Sentiment": sentiment,
                                "Tone": tone,
                                "Intention": intention
                            },
                            customer_question=customer_question,
                        )
                        llm_response = generate_llm_response(
                            customer_data={
                                "Name": customer_name,
                                "LastDealStatus": "New",
                                "Notes": "No prior interactions.",
                                "Sentiment": sentiment,
                                "Tone": tone,
                                "Intention": intention
                            },
                            recommendations=recommendations,
                            customer_question=customer_question,
                        )
                        # Generate post-call summary
                        summary = post_call_summary(
                            customer_data={
                                "Name": customer_name,
                                "LastDealStatus": "New",
                                "Notes": "New customer",
                                "Sentiment": sentiment,
                                "Tone": tone,
                                "Intention": intention,
                            },
                            recommendations=recommendations,
                            customer_question=customer_question,
                            llm_response=llm_response
                        )

                        # Add the new customer to the database with post-call summary
                        add_customer_to_db(
                            name=customer_name,
                            email="unknown@example.com",
                            phone="0000000000",
                            sentiment=sentiment,
                            tone=tone,
                            intention=intention,
                            notes=summary,
                            recommendations=recommendations  
                        )
                        st.write(f"Customer '{customer_name}' added successfully with a new ID!") 
                        st.write("### Assistant Response:")
                        st.write(llm_response)
                    else:
                        st.warning("Please provide a query or additional information for the new customer.")
        else:
            st.warning("Please enter a valid customer name.")

    
    if st.button("process the Negotiations"):
        if customer_name.strip():
            customer_data = fetch_customer_data(customer_name)
            if customer_data:
                customer_id = customer_data.get("CustomerID")
                if f'conversation_{customer_id}' not in st.session_state:
                    st.session_state[f'conversation_{customer_id}'] = []
                if f'negotiation_history_{customer_id}' not in st.session_state:
                    st.session_state[f'negotiation_history_{customer_id}'] = []
                

                if not st.session_state[f'negotiation_history_{customer_id}']:
                    with st.spinner("Generating initial negotiation tips..."):
                        initial_tips = negotiation_assistant(
                        customer_name=customer_data.get('Name', 'Customer'),
                        sentiment=customer_data.get("Sentiment", "Neutral"),
                        tone=customer_data.get("Tone", "Neutral"),
                        recommendation=customer_data.get("RecommendedDeal", "No recommendations provided."),
                        current_discount=5,
                        max_discount=40,
                        customer_query1="No previous query",
                        his_negotiation="No previous negotiation history.",
                        negotiation_result="newly strated the negotiotion"
                    )
                    st.session_state[f'negotiation_history_{customer_id}'].append(initial_tips)
                    st.write(initial_tips)
                # Ask for customer input after generating initial tips
                user_input = st.text_input(
                    "Enter customer's query or response:",
                    key=f"user_input_{customer_id}",
                    on_change=partial(handle_input, customer_data)
                )
                # Process user input if provided
                if user_input:
                    handle_input(customer_data)

                if st.session_state[f'conversation_{customer_id}']:
                    st.write("### Conversation History")
                    for message in st.session_state[f'conversation_{customer_id}']:
                        st.write(message)
            else:
                st.error("Customer not found. Please check the name and try again.")
        else:
            st.warning("Please enter a valid customer name.")


                


        
# Customer Info Page
def customer_info():
    st.title("Customer Info")
    st.sidebar.markdown("# Customer Info")

    def fetch_all_customer_info():
        """
        Fetch all customer information from the database.
        """
        conn = get_db_connection()
        query = """
        SELECT c.CustomerID, c.Name, c.Email, c.Phone, 
               ih.LastDealStatus, ih.InteractionDate, ih.Notes, 
               ih.Sentiment, ih.Tone, ih.Intention
        FROM Customers c
        LEFT JOIN InteractionHistory ih ON c.CustomerID = ih.CustomerID
        ORDER BY c.Name
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # Fetch and display customer data
    customer_data = fetch_all_customer_info()

    if not customer_data.empty:
        st.subheader("All Customer Information:")
        st.dataframe(customer_data, use_container_width=True)  # Display as a scrollable table
    else:
        st.warning("No customer information found in the database.")   
    st.link_button("Available Cars", "https://docs.google.com/spreadsheets/d/1-58GuEG2SXQZsKnpgM4yrhFPTrKceV9-YiInbzN2Zks/edit?usp=sharing")
    st.link_button("Performance Metrics", "https://docs.google.com/spreadsheets/d/1J-i0pewj3YqQ4l4TJc0HH8471Sodzop2937c1JHMO9I/edit?usp=sharing")

if __name__ == "__main__":
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select a page", ["Home", "Customer Info"])

    st.sidebar.header("Interaction History")
    st.sidebar.line_chart(Sinteraction_history.set_index("Step")[["Sentiment", "Tone"]])
    
    if page == "Home":
        home_page()
    elif page == "Customer Info":
        customer_info()
