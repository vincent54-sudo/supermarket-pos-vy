import json
import sqlite3

# Load the JSON data
with open('inventory.json', 'r') as f:
    products = json.load(f)

# Connect to your database
conn = sqlite3.connect('supermarket.db')
cursor = conn.cursor()

# Insert products
for p in products:
    cursor.execute("""
        INSERT OR IGNORE INTO products (id, name, category, stock, price, barcode)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (p['id'], p['name'], p['category'], p['stock'], p['price'], p['barcode']))

conn.commit()
conn.close()
print("Database Seeded Successfully!")