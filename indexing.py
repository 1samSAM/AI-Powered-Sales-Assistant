import os
from dotenv import load_dotenv
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
load_dotenv(dotenv_path="config.env")

# Set Hugging Face API key
os.environ["HUGGINGFACE_API_KEY"] = os.getenv("HUGGINGFACE_API_KEY")

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Initialize FAISS vector store globally (empty at the start)
vector_store = None

def ingest_product_data(xlsx_path: str):
    """
    Ingest product data from an XLSX file and add it to the FAISS vector store.
    Args:
        xlsx_path (str): Path to the XLSX file containing product data.
    """
    global vector_store

    try:
        # Read product data from Excel file
        product_data = pd.read_excel(xlsx_path)
        
        # Required columns
        required_columns = [
            "Name", "Location", "Year", "Kilometers_Driven", "Fuel_Type", 
            "Transmission", "Owner_Type", "Mileage", "Engine", "Power", 
            "Seats", "Price"
        ]
        
        # Validate required columns
        for col in required_columns:
            if col not in product_data.columns:
                raise KeyError(f"Missing required column: {col}")
        
        # Generate text representations
        product_texts = product_data.apply(
            lambda row: (
                f"Name: {row['Name']} | Location: {row['Location']} | Year: {row['Year']} | "
                f"Kilometers Driven: {row['Kilometers_Driven']} | Fuel Type: {row['Fuel_Type']} | "
                f"Transmission: {row['Transmission']} | Owner Type: {row['Owner_Type']} | "
                f"Mileage: {row['Mileage']} | Engine: {row['Engine']} | Power: {row['Power']} | "
                f"Seats: {row['Seats']} | Price: {row['Price']} lakhs"
            ),
            axis=1
        ).tolist()
        
        # Add texts to FAISS vector store
        vector_store = FAISS.from_texts(product_texts, embeddings)
        print(f"Indexed {len(product_texts)} product records.")
    except FileNotFoundError:
        print(f"Error: File '{xlsx_path}' not found. Please check the path and try again.")
    except KeyError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during ingestion: {e}")

def save_index(index_file: str):
    """
    Save the FAISS vector store index to a file.
    Args:
        index_file (str): Path to save the index file.
    """
    try:
        if vector_store:
            vector_store.save_local(index_file)
            print(f"Index successfully saved to '{index_file}'.")
        else:
            print("No vector store to save.")
    except Exception as e:
        print(f"Error saving index: {e}")

def load_index(index_file: str):
    """
    Load the vector store index from a file.
    Args:
        index_file (str): Path to the saved index file.
    """
    try:
        # Enable dangerous deserialization explicitly
        vector_store = FAISS.load_local(index_file, embeddings, allow_dangerous_deserialization=True)
        print(f"Index successfully loaded from '{index_file}'.")
        return vector_store
    except Exception as e:
        print(f"Error loading index: {e}")
        return None

if __name__ == "__main__":
    # Paths for data and index
    product_xlsx = "product_details.xlsx"  # Replace with your Excel file path
    index_output = "vector_store_index"   # Desired FAISS index file name

    # Ingest data and save index
    print("Starting product data ingestion...")
    ingest_product_data(product_xlsx)
    
    print("Saving the vector store index...")
    save_index(index_output)
    
    # Load the index
    print("Loading the vector store index...")
    loaded_vector_store = load_index(index_output)