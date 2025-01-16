import sqlite3
from datetime import datetime

# Database path
DB_PATH = "SalesCRM.db"

# Sample customer details
customers = [
    {"Name": "John Doe", "Email": "johndoe@example.com", "Phone": "1234567890"},
    {"Name": "Jane Smith", "Email": "janesmith@example.com", "Phone": "9876543210"},
    {"Name": "Alice Brown", "Email": "alicebrown@example.com", "Phone": "4561237890"},
    {"Name": "Robert White", "Email": "robertwhite@example.com", "Phone": "7891234560"},
    {"Name": "Emily Green", "Email": "emilygreen@example.com", "Phone": "3217894560"},
]

# Sample interaction history
timestamps = [
    "2024-12-20 14:30:00",
    "2024-12-19 10:15:00",
    "2024-12-18 16:45:00",
    "2024-12-17 12:00:00",
    "2024-12-16 09:20:00",
]
interaction_history = [
    {"LastDealStatus": "Closed-Won", "Notes": "Interested in budget cars", "Sentiment": "Positive", "Tone": "Happy", "Intention": "Purchase"},
    {"LastDealStatus": "Closed-Lost", "Notes": "Looking for high mileage cars", "Sentiment": "Neutral", "Tone": "Concerned", "Intention": "Inquiry"},
    {"LastDealStatus": "Pending", "Notes": "Needs more details", "Sentiment": "Negative", "Tone": "Angry", "Intention": "Complaint"},
    {"LastDealStatus": "Negotiation", "Notes": "Asked for discounts", "Sentiment": "Positive", "Tone": "Happy", "Intention": "Purchase"},
    {"LastDealStatus": "Follow-Up", "Notes": "Waiting for confirmation", "Sentiment": "Neutral", "Tone": "Concerned", "Intention": "Inquiry"},
]

# Insert data into database
def populate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert customers
    for customer in customers:
        cursor.execute(
            """
            INSERT INTO Customers (Name, Email, Phone)
            VALUES (?, ?, ?)
            """,
            (customer["Name"], customer["Email"], customer["Phone"]),
        )

    # Retrieve customer IDs
    cursor.execute("SELECT CustomerID FROM Customers")
    customer_ids = [row[0] for row in cursor.fetchall()]

    # Insert interaction history
    for idx, history in enumerate(interaction_history):
        cursor.execute(
            """
            INSERT INTO InteractionHistory (CustomerID, LastDealStatus, InteractionDate, Notes, Sentiment, Tone, Intention)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_ids[idx],
                history["LastDealStatus"],
                timestamps[idx],
                history["Notes"],
                history["Sentiment"],
                history["Tone"],
                history["Intention"],
            ),
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    populate_database()
    print("Database populated successfully with sample customer data.")
