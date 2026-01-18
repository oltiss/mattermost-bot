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

from typing import List, Optional

@mcp.tool()
def get_database_schema(schema: str = "public", table_name: Optional[str] = None) -> str:
    """
    Pobiera schemat bazy danych.
    1. Jeśli `table_name` nie jest podane: zwraca listę wszystkich tabel i widoków w danym schemacie.
    2. Jeśli `table_name` jest podane: zwraca listę kolumn i typów danych dla tej tabeli/widoku.

    Używaj tego narzędzia, aby zrozumieć strukturę bazy danych przed utworzeniem zapytania SQL.
    """
    return _get_database_schema_logic(schema, table_name)

def _get_database_schema_logic(schema: str = "public", table_name: str = None) -> str:
    # Handle empty strings from LLM as defaults
    if not schema:
        schema = "public"
    if not table_name:
        table_name = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if table_name:
            # Pobierz szczegóły kolumn dla konkretnej tabeli
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """
            cur.execute(query, (schema, table_name))
            rows = cur.fetchall()

            if not rows:
                return f"Nie znaleziono tabeli o nazwie '{table_name}' w schemacie '{schema}'."

            result = f"Struktura tabeli '{table_name}' (schemat: {schema}):\n"
            result += "Kolumna | Typ Danych | Czy Null?\n"
            result += "-" * 40 + "\n"
            for row in rows:
                result += f"{row[0]} | {row[1]} | {row[2]}\n"

        else:
            # Pobierz listę wszystkich tabel i widoków
            query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name;
            """
            cur.execute(query, (schema,))
            rows = cur.fetchall()

            if not rows:
                return f"Nie znaleziono żadnych tabel w schemacie '{schema}'."

            result = f"Lista tabel i widoków w schemacie '{schema}':\n"
            result += "Nazwa Tabeli | Typ\n"
            result += "-" * 30 + "\n"
            for row in rows:
                result += f"{row[0]} | {row[1]}\n"

        cur.close()
        conn.close()
        return result

    except Exception as e:
        return f"Błąd podczas pobierania schematu: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000, host="0.0.0.0")
