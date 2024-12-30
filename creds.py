import gspread
from google.oauth2.service_account import Credentials

# Define the scope of access
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 
          "https://www.googleapis.com/auth/drive"]

# Path to your JSON key file
SERVICE_ACCOUNT_FILE = "alert-rush-445806-v2-9f9cb653e266.json"

# Authenticate using the JSON key file
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Authorize the client
client = gspread.authorize(credentials)

# Access your Google Sheet
sheet = client.open("my project").sheet1

# Example: Update a cell
sheet.update_cell(1, 1, "Hello, World!")

# Example: Read all records
records = sheet.get_all_records()
print(records)
