import hashlib
import sqlite3

def connect_db():
    # Open and connect to database to run SQL
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Initialize users.db with 3 columns if doesn't exist 
    c.execute('''CREATE TABLE IF NOT EXISTS users
              (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    
    # Disconnect from database
    conn.commit()
    conn.close()


def register_user(username, password):
    # Open and connect to database to run SQL
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Encode password, add username and hashed password to DB
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, hashed_pw))
    
    # Disconnect from database
    conn.commit()
    conn.close()


def authenticate(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, hashed_pw))

    user = c.fetchone()
    conn.close()

    return True if user else False