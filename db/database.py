from mysql import connector
from .configuration import get_database_configuration


def get_connection():
    return connector.connect(**get_database_configuration())


def fetch_all(query, params=()):
    """Esegue una SELECT e restituisce tutte le righe come dizionari."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        connection.close()


def fetch_one(query, params=()):
    """Esegue una SELECT e restituisce la prima riga (o None)."""
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query, params=()):
    """Esegue INSERT/UPDATE/DELETE, fa il commit e restituisce l'id inserito."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()