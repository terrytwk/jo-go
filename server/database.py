import sqlite3

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'

def create_database():
    """
    Connect to the JOGO_DB_LOCATION (declared globally) database. Create the jogo.db database and tables if they don't exist.
        id := encrypted user's id, used for authorizing users

    Returns:
        None
    """
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    # users table
    # id := encrypted user's student ID
    # user_type := enum {"student", "staff"} 
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (id text, token text, kerb text, first_name text, last_name text, user_type text, created_at timestamp);''')
    
    # items table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS items (id text, item_name text, item_count int);'''
    )

    # item_limits table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS item_limits (item_name text, max_limit int);'''
    )

    # history table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS history (id text, item_name text, action text);'''
    )

    # swipe table
    # stores currently tapped in user's token  
    c.execute(
        '''CREATE TABLE IF NOT EXISTS swipe (token text);'''
    )

    conn.commit()
    conn.close()
