import sqlite3
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # Create login table
    db.execute('''
        CREATE TABLE IF NOT EXISTS Rubrica_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create rubrica table
    db.execute('''
        CREATE TABLE IF NOT EXISTS Rubrica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            sesso TEXT NOT NULL,
            data_nascita TEXT,
            telefono TEXT,
            email TEXT NOT NULL,
            citta TEXT,
            utente_id INTEGER,
            FOREIGN KEY (utente_id) REFERENCES Rubrica_login(id)
        )
    ''')
    
    db.commit()