import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Drop existing users table to update the schema
cursor.execute("DROP TABLE IF EXISTS users")

cursor.execute("""
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user',
    profile_photo TEXT DEFAULT 'static/images/default_profile.png',
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    image_path TEXT,
    disease_name TEXT,
    confidence REAL,
    solution_name TEXT,
    severity TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Migration: check if severity column exists in history table, add if it doesn't
try:
    cursor.execute("SELECT severity FROM history LIMIT 1")
except sqlite3.OperationalError:
    # column doesn't exist, alter table to add it
    cursor.execute("ALTER TABLE history ADD COLUMN severity TEXT")

# Create Labor Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS labor(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    name TEXT,
    role TEXT,
    wage REAL,
    contact TEXT
)
""")

# Create Tasks & Irrigation Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    description TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'pending'
)
""")

# Create GPS Farm Plots Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS plots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    name TEXT,
    area REAL,
    coordinates TEXT
)
""")

# Create Financials / Cost-Profit Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS financials(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    crop_name TEXT,
    labor_cost REAL,
    fertilizer_cost REAL,
    pesticide_cost REAL,
    other_cost REAL,
    expected_revenue REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Seed default accounts
default_users = [
    ("System Administrator", "admin@smartcrop.com", "admin123", "admin"),
    ("Ramesh Kumar (Farmer)", "farmer@smartcrop.com", "farmer123", "user")
]

for fullname, email, password, role in default_users:
    try:
        if role == 'user':
            cursor.execute("""
                INSERT INTO users (fullname, email, password)
                VALUES (?, ?, ?)
            """, (fullname, email, password))
        else:
            cursor.execute("""
                INSERT INTO users (fullname, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (fullname, email, password, role))
    except sqlite3.IntegrityError:
        # Already exists
        pass

conn.commit()
conn.close()

print("Database created and seeded successfully with extended schemas.")