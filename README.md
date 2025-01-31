# AI-Powered Sales Assistant

This is a real-time AI-powered sales assistant that leverages speech-to-text, sentiment analysis, tone detection, and fuzzy product matching to provide dynamic price recommendations for customers. The application integrates with Google Sheets for data storage and uses SQLite for product information.

---

## Features
- **Speech Recognition**: Converts user speech into text using Google Speech Recognition API.
- **Sentiment Analysis**: Identifies the customer's sentiment (positive, neutral, or negative) using Hugging Face's NLP pipelines.
- **Tone Detection**: Detects the emotional tone of the customer (e.g., sadness, happiness, excitement).
- **Fuzzy Product Matching**: Matches products even when the input is not an exact match using RapidFuzz.
- **Dynamic Price Recommendations**: Calculates the best price based on customer sentiment and tone.
- **Google Sheets Integration**: Saves interaction data, including sentiment, tone, and price recommendations, to a Google Sheet for tracking and analysis.
- **SQLite Database**: Manages product data with attributes like name, category, price, and stock status.

---

## Requirements

### Python Libraries
Install the required Python libraries using the following command:
```bash
pip install -r requirements.txt
```
## Dependencies
Flask
Flask-SocketIO
google-auth
gspread
sqlite3
speechrecognition
transformers
rapidfuzz
## Setup Instructions
1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-powered-sales-assistant.git
cd ai-powered-sales-assistant
```
2. Configure Google Sheets API
Set up a Google Cloud project and enable the Google Sheets and Drive APIs.
Download the service account credentials file (service_account.json) and save it in the project directory.
3. Prepare the SQLite Database
Create a SQLite database file named crm.db.

Add a table named products with the following structure:

```sql
Copy code
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    start_price REAL NOT NULL,
    limit_price REAL NOT NULL,
    stock_status TEXT NOT NULL
);
```
```sql
Populate the products table with sample data:

sql
Copy code
INSERT INTO products (name, category, start_price, limit_price, stock_status)
VALUES
    ('Laptop', 'Electronics', 500.00, 450.00, 'In Stock'),
    ('Phone', 'Electronics', 300.00, 250.00, 'In Stock'),
    ('Tablet', 'Electronics', 200.00, 180.00, 'In Stock');
```
4. Run the Application
```bash
Copy code
python app.py
```
5. Access the Application
Open your browser and navigate to http://localhost:5000.

## Usage
### Start Listening
1. Click the Start Listening button to begin capturing audio.
2. Speak into your microphone to describe your product needs (e.g., "I want a laptop").
3. The assistant will transcribe your speech, analyze your sentiment and tone, and provide a dynamic price recommendation.
### Stop Listening
Click the Stop Listening button to end the interaction.

## Project Structure

Below is the structure of the project and a brief description of each file:

### **Database**
- **`SalesCRM.db`**  
  The main database that stores customer details, product information, negotiation history, and other key data required for CRM operations.

- **`crm_database_create.py`**  
  Script for creating and initializing the `SalesCRM.db` database, including tables for customers, products, and negotiation logs.

### **Core Scripts**
- **`indexing.py`**  
  Handles vector creation and indexing using embeddings for product details. This is crucial for similarity search and retrieval in the RAG (Retrieval-Augmented Generation) framework.

- **`main.py`**  
  The main entry point for the application. Integrates all modules and orchestrates the overall workflow, including user interface and backend functionalities.

- **`negotiation.py`**  
  Contains logic for the AI-powered negotiation assistant, which uses sentiment, tone, and real-time customer input to drive intelligent deal recommendations.

### **Utilities**
- **`product_details.xlsx`**  
  A dataset containing 200 car details such as model names, features, and prices. This file is used for recommendation and negotiation.

- **`requirements.txt`**  
  A list of dependencies required to run the project. Use the following command to install them:
  ```bash
  pip install -r requirements.txt


## Acknowledgments
Hugging Face for their amazing NLP models.
Google Cloud for the Sheets API.
SQLite for lightweight database management.
Contribution
Pull requests are welcome! For major changes, please open an issue to discuss your proposed changes first.
