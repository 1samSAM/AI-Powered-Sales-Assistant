import sqlite3

def create_crm_database():
    try:
        # Connect to SQLite database (it will create the file if it doesn't exist)
        connection = sqlite3.connect("SalesCRM.db")
        cursor = connection.cursor()

        # Create Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Customers (
                CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Email TEXT,
                Phone TEXT
            )
        ''')

        # Create InteractionHistory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS InteractionHistory (
                InteractionID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID INTEGER,
                LastDealStatus TEXT,
                InteractionDate TEXT,
                Notes TEXT,
                Intention TEXT,
                Sentiment TEXT,   -- e.g., Positive, Negative, Neutral
                Tone TEXT,        -- e.g., Happy, Angry, Concerned
                FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
            )
        ''')

        # Create Recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Recommendations (
                RecommendationID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID INTEGER,
                RecommendedDeal TEXT,
                Date TEXT,
                FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
            )
        ''')

        print("CRM database and tables created successfully!")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if connection:
            connection.commit()
            connection.close()

# Call the function to create the database
if __name__ == "__main__":
    create_crm_database()
