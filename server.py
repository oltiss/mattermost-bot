# server.py
from fastmcp import FastMCP
import os
import psycopg2
from dotenv import load_dotenv

# Wczytaj zmienne środowiskowe
load_dotenv()

# Inicjalizacja serwera
mcp = FastMCP("Mój Serwer Lokalny")

# Konfiguracja bazy danych
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

@mcp.tool()
def query_database(query: str) -> str:
    """
    Wykonuje zapytanie SQL do bazy danych PostgreSQL.
    Narzędzie działa w trybie TYLKO DO ODCZYTU.
    Dozwolone są tylko zapytania SELECT.
    """
    # 1. Wstępna walidacja zapytania
    if not query.strip().upper().startswith("SELECT"):
        return "Błąd: Dozwolone są tylko zapytania typu SELECT (tryb read-only)."

    try:
        conn = get_db_connection()
        # 2. Ustawienie sesji na read-only (dodatkowe zabezpieczenie po stronie bazy)
        conn.set_session(readonly=True)

        cur = conn.cursor()
        cur.execute(query)

        if cur.description:
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            result = f"Kolumny: {', '.join(columns)}\n"
            for row in rows:
                result += f"{str(row)}\n"

            conn.commit()
            cur.close()
            conn.close()
            return result
        else:
            conn.commit()
            cur.close()
            conn.close()
            return "Brak danych."

    except Exception as e:
        return f"Błąd bazy danych: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
