import sqlite3
from typing import List, Dict, Any
import json

DB_PATH = "/home/myhome/myHomeAssistant_dashboard/prisma/dev.db" 

def get_connection():
    """Creează o conexiune la baza de date SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

def get_all_devices() -> List[Dict[str, Any]]:
    """Obține toate dispozitivele din baza de date"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Device")  
    devices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return devices