import gspread
import streamlit as st
import time
import pandas as pd
import uuid
from utils import analyze_tone, analyze_sentiment, llm
from googleapiclient.discovery import build
from langchain.schema import HumanMessage
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build



SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = "alert.json"

# Google Sheets Authentication
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet = client.open("my project").sheet1


# Access Google Sheet


# Function to update performance metrics in Google Sheets
def update_performance_metrics(sheet_id, customer_name, sales_rep, negotiation_result, tone, sentiment, notes):
    try:
        # Define the row data to insert
        row_data = [str(sheet_id), str(customer_name), str(sales_rep), str(negotiation_result), str(tone), str(sentiment), str(notes), time.strftime("%Y-%m-%d %H:%M:%S")]

        # Append data to the Google Sheet
        sheet.append_row(row_data)
        st.success("Performance metrics updated successfully!")
    except Exception as e:
        st.error(f"Error updating Google Sheets: {e}")




def negotiation_assistant(
    customer_name, sentiment, tone, recommendation, current_discount, max_discount, customer_query1, his_negotiation, negotiation_result
):
    """
    AI generates concise negotiation tips with relevant car details, pricing, and negotiation logic.
    The LLM calculates discounts and provides seller-focused suggestions to close the deal.
    """
    prompt = f"""
        INSTRUCTIONS:
        -- You are an AI assistant representing the seller in a car negotiation.
        -- The customer '{customer_name}' has shown interest in the following recommendations:
        {recommendation}
        -- Your goal is to dynamically retrieve details like price, features, and calculate appropriate discounts while ensuring continuity with previous discussions.
        -- the {negotiation_result} contain the current negotiation result, the respones should be consider the "Continue Negotiation", "Close Deal", "End Negotiation"

        OBJECTIVES:
        1. Retrieve key details for each recommended car (name, price, features).
        2. Start with the current discount of {current_discount}% and ensure the maximum discount does not exceed {max_discount}%.
        3. Consider the customer's input: "{customer_query1}" to address specific concerns and preferences.
        4. Use the previous negotiation response: "{his_negotiation}" to ensure continuity and personalized engagement.
        5. Generate a focused response prioritizing customer satisfaction while maintaining profitability.

        CUSTOMER CONTEXT:
        -- Sentiment: {sentiment}
        -- Tone: {tone}
        -- Customer Input: {customer_query1}

        RESPONSE FORMAT:
        1. Key Highlights: Provide a brief summary of the car details with calculated prices after the current discount.
        2. Justification: Offer one or two strong reasons for the pricing based on features, benefits, and offers.
        3. Seller Recommendation: Suggest one actionable next step to secure the deal.
        4. Tips for the Seller: Provide two concise, actionable tips to help close the deal based on the customer's sentiment and tone.

        BEGIN RESPONSE:
    """

    try:
        # Invoke LLM to handle negotiation logic
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        st.error(f"Error generating negotiation tips: {e}")
        return "Unable to generate tips. Please try again."


def generate_sales(last_message):
    """
    Generates car names and their corresponding prices based on the last message.
    
    Args:
        last_message (str): The last message from the conversation that may contain customer preferences or queries.
    
    Returns:
        list: A list of tuples containing car names and their prices.
    """
    # Define the prompt for the AI model
    prompt = f"""
    You are a car sales assistant. Based on the following customer message, generate a list of car names and their corresponding prices:
    
    Customer Message: "{last_message}"
    
    Please provide the car names and prices in the following format:
    - Car Name 1: $Price1
    - Car Name 2: $Price2

    Generate the structured cars and its price directly without adding unnecessary introductions or conclusions.
    """

    try:
        # Invoke the language model to generate the response
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        st.error(f"Error generating car sales information: {e}")
        return []

def generate_notes(last_message):
    """
    Generates a very short summary based on the last message.
    """
    
    # Define the prompt for the AI model
    prompt = f"""
    You are a summarization assistant. Based on the following customer message, generate a very short summary or notes:
    
    Customer Message: "{last_message}"
    
    Please provide a concise summary in one or two sentences.
    Generate the structured summary directly without adding unnecessary introductions or conclusions.
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        st.error(f"Error generating notes: {e}")
        return "Unable to generate notes."



# Function to handle user input and manage negotiation flow
def handle_input(customer_data):
    # Initialize session state for negotiation history and conversation
    customer_id = customer_data['CustomerID']
    if f'conversation_{customer_id}' not in st.session_state:
        st.session_state[f'conversation_{customer_id}'] = []
    if f'negotiation_history_{customer_id}' not in st.session_state:
        st.session_state[f'negotiation_history_{customer_id}'] = []
    # Initialize session state for the selected option
    #if f'selected_option_{customer_id}' not in st.session_state:
    #    st.session_state[f'selected_option_{customer_id}'] = None

    # Extract customer details
    customer_name = customer_data.get('Name', 'Customer')
    recommendation = customer_data.get("RecommendedDeal", "No recommendations provided.")
    sentiment = customer_data.get("Sentiment", "Neutral")
    tone = customer_data.get("Tone", "Neutral")

    """# Display negotiation options
    option_map = {
        0: "Continue Negotiation",
        1: "Close Deal",
        2: "End Negotiation",
    }

    # Display the pills widget and update session state on selection
    selection = st.pills(
        "Select Negotiation Action",
        options=(option_map.keys()),
        format_func=lambda option: option_map[option],
        key=f"pills_{customer_id}",  # Unique key for each customer
        selection_mode="single",
    )


    # Update session state if a new option is selected
    if selection is not None:
        st.session_state[f'selected_option_{customer_id}'] = selection

    # Get the selected option from session state
    selected_option = st.session_state[f'selected_option_{customer_id}']

    # Handle the case where no option is selected
    if selected_option is None:
        st.warning("Please select a negotiation action to proceed.")
        return  # Exit the function early if no option is selected

    # Display the selected option
    negotiation_result = selected_option
    """

   

    # Retrieve user input from session state
    user_input = st.session_state.get(f"user_input_{customer_id}", "")
    if user_input:
         # Ensure st.session_state[f'conversation_{customer_id}'] is a list
        if not isinstance(st.session_state[f'conversation_{customer_id}'], list):
            st.session_state[f'conversation_{customer_id}'] = []
        st.session_state[f'conversation_{customer_id}'].append(f"### You: {user_input}")


        # Analyze sentiment and tone of the user input
        sentiment = analyze_sentiment(user_input)
        tone = analyze_tone(user_input)

        # Generate updated negotiation tips
        tips = negotiation_assistant(
            customer_name=customer_name,
            sentiment=sentiment,
            tone=tone,
            recommendation=recommendation,
            current_discount=5,
            max_discount=40,
            customer_query1=user_input,
            his_negotiation=st.session_state[f'negotiation_history_{customer_id}'][-1] if st.session_state[f'negotiation_history_{customer_id}'] else "",
            negotiation_result="newty strated the negotiotion"
        )
        st.session_state[f'conversation_{customer_id}'].append(f"### Bot: {tips}")
        st.session_state[f'negotiation_history_{customer_id}'].append(tips)

        # Display the updated conversation
        st.write(tips)

    

    # Generate sales and notes for performance metrics
    if st.session_state[f'conversation_{customer_id}']:
        last_message = st.session_state[f'conversation_{customer_id}'][-1]
        sales_rep = generate_sales(last_message)
        notes = generate_notes(last_message)
        update_performance_metrics(
            sheet_id="sam",
            customer_name=customer_name,
            sales_rep=sales_rep,
            negotiation_result= "negotiating",
            tone=tone,
            sentiment=sentiment,
            notes=notes
        )

    
    
    











#           if negotiation_result == "Continue Negotiation":
#
#            user_input = st.session_state.user_query
#            if user_input:
#
#                # Append user input to the conversation history
#               st.session_state[f'conversation_{customer_id}'].append(f"### You: {user_input}")
#
#               # Analyze sentiment and tone of the user input
#                sentiment = analyze_sentiment(user_input)
#                tone = analyze_tone(user_input)
#
#                # Generate updated negotiation tips
#                tips = negotiation_assistant(
#                    customer_name=customer_name,
#                    sentiment=sentiment,
#                    tone=tone,
#                    recommendation=recommendation,
#                    current_discount=st.session_state.current_discount,
#                    max_discount=40,  # Maximum discount
#                    customer_query1=user_input,
#                    his_negotiation=st.session_state[f'negotiation_history_{customer_id}'][-1] if st.session_state[f'negotiation_history_{customer_id}'] else ""
#               )
#            
#            # Append the bot's response to the conversation and negotiation history
#            st.session_state[f'conversation_{customer_id}'].append(f"### Bot: {tips}")
#            st.session_state[f'negotiation_history_{customer_id}'].append(tips)
#            st.session_state.user_query = ""  # Clear input after submission
#   
#    # Display the conversation history for the specific customer
#    if st.session_state[f'conversation_{customer_id}']:
#        last_message = st.session_state[f'conversation_{customer_id}'][-1]  # Get the last message
#        st.write(last_message)
#        sales_rep = generate_sales(last_message)
#        notes = generate_notes(last_message)
#        sheet_id="sam"
#        update_performance_metrics(sheet_id, customer_name, sales_rep, negotiation_result, tone, sentiment, notes)
#    
#    
#    if negotiation_result in ["Close Deal", "End Negotiation"]:
#        st.write("The negotiation has been concluded.")
#        return
    