import sqlite3

def init_crm_database():
    """
    Initialize the CRM database with sample product data.
    """
    # Connect to the database
    connection = sqlite3.connect("crm.db")
    cursor = connection.cursor()

    # Create the products table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            start_price REAL,
            price_limit REAL,
            availability TEXT
        )
    """)

    # Clear any existing data in the products table
    cursor.execute("DELETE FROM products")

    # Sample product data to populate the table
    products = [
        ("Laptop", "Electronics", 500, 450, "In Stock"),
        ("Phone", "Electronics", 300, 250, "In Stock"),
        ("Tablet", "Electronics", 200, 180, "Out of Stock"),
        ("Smartwatch", "Accessories", 150, 130, "In Stock"),
        ("Camera", "Electronics", 400, 350, "In Stock"),
        ("Headphones", "Accessories", 100, 80, "In Stock"),
        ("Speaker", "Electronics", 120, 100, "Out of Stock"),
        ("Monitor", "Electronics", 250, 200, "In Stock"),
        ("Keyboard", "Accessories", 50, 40, "In Stock"),
        ("Mouse", "Accessories", 30, 25, "In Stock")
    ]

    # Insert the sample data into the products table
    cursor.executemany("""
        INSERT INTO products (name, category, start_price, price_limit, availability)
        VALUES (?, ?, ?, ?, ?)
    """, products)

    # Commit the changes and close the connection
    connection.commit()
    connection.close()
    print("CRM database initialized successfully.")

# Call the function when running this script
if __name__ == "__main__":
    init_crm_database()
