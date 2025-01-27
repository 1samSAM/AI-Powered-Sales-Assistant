import streamlit as st
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from a .env file
load_dotenv(dotenv_path="config.env")

# API Key for Groq
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("API key for Groq is not set. Please provide a valid key.")

# Initialize Groq Model
try:
    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)
    print("Groq model initialized successfully!")
except Exception as e:
    raise RuntimeError(f"Error initializing the Groq model: {e}")


# Paths
DB_PATH = "SalesCRM.db"
VECTOR_STORE_PATH = "vector_store_index"


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


def fetch_customer_data(customer_name):
    """
    Fetch customer details and interaction history from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.CustomerID, c.Name, c.Email, c.Phone, 
               ih.LastDealStatus, ih.InteractionDate, ih.Notes, ih.Sentiment, ih.Tone, ih.Intention
        FROM Customers c
        LEFT JOIN InteractionHistory ih ON c.CustomerID = ih.CustomerID
        WHERE c.Name = ?
        ORDER BY ih.InteractionDate DESC
        LIMIT 1
        """,
        (customer_name,),
    )
    customer = cursor.fetchone()
    conn.close()

    if customer:
        columns = [
            "CustomerID", "Name", "Email", "Phone", "LastDealStatus",
            "InteractionDate", "Notes", "Sentiment", "Tone", "Intention"
        ]
        return dict(zip(columns, customer))
    return None


def recommend_deals(customer_data):
    """Generate personalized car recommendations."""
    query = {
        "purchase": f"Budget-friendly cars, suitable for {customer_data.get('Tone', 'Neutral')} tone customers.",
        "inquiry": "Recent models from 2015 onwards",
        "general": "General product recommendations",
    }.get(customer_data.get("Intention", "general").lower(), "General product recommendations")

    try:
        # Check if the vector store has data
        if vector_store and len(vector_store.docstore._dict) > 0:  # Use FAISS-specific method to check index size
            results = vector_store.similarity_search(query, k=2)
            recommendations = "\n".join(
                f"{i+1}. {result.page_content.strip()}" for i, result in enumerate(results)
            )
        else:
            recommendations = "Fallback: Based on your input, consider our latest car models."
        return f"Based on the customer's profile, we recommend:\n\n{recommendations}"
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return "No recommendations available."




def generate_llm_response(customer_data, recommendations):
    """Generate AI response for the sales assistant."""
    # Format the customer data and recommendations into a single prompt
    prompt = f"""
    You are a professional sales assistant. Based on the customer profile and recommendations, 
    generate a point-by-point summary of the last interaction in a professional tone. 
    The summary should be concise yet detailed, focusing on key points relevant to the customer's needs and concerns. 

    Additionally, craft a set of clear, engaging, and concise instructions that the salesperson can use 
    to communicate the recommendations effectively to the customer. 
    These instructions should:
    - Highlight the customer's preferences.
    - Address their concerns.
    - Encourage further action.
    - Be phrased in a friendly and approachable manner.
    - Remain short and to the point.

    All instructions should guide the salesperson on what to say directly to the custome

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
    
    Provide a clear, concise, and actionable response for the salesperson.

    """

    # Use the `llm` object to invoke the model
    try:
        response = llm.invoke(prompt)
        return response.content  # Extract content from the LLM response
    except Exception as e:
        st.error(f"Error generating AI response: {e}")
        return "Unable to generate a response. Please try again."




# Main App
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page", ["Home", "Customer Info"])

if page == "Home":
    st.title("AI Sales Assistant")
    st.sidebar.title("Customer Query")

    customer_name = st.text_input("Enter the customer's name:", placeholder="e.g., Jane Smith")

    # New Input: Customer Question or Additional Information
    customer_question = st.text_area(
        "Enter any question, doubt, or additional information from the customer:",
        placeholder="e.g., Can I get a discount on this car?",
    )

    if st.button("Get Recommendations"):
        if customer_name.strip():
            with st.spinner("Fetching data and generating recommendations..."):
                customer_data = fetch_customer_data(customer_name)
                if customer_data:
                    recommendations = recommend_deals(customer_data)
                    llm_response = generate_llm_response(customer_data, recommendations)
                    st.markdown(f"### Recommendations for {customer_name}:")
                    st.markdown(recommendations)
                    st.markdown(f"### Assistant Response:\n{llm_response}")
                else:
                    st.warning(f"No data found for customer '{customer_name}'. Please check the name.")
        else:
            st.warning("Please enter a valid customer name.")

# Customer Info Page
elif page == "Customer Info":
    st.title("Customer Info")
    st.sidebar.markdown("# Customer Info")

    def fetch_all_customer_info():
        """
        Fetch all customer information from the database.
        """
        conn = sqlite3.connect(DB_PATH)
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




