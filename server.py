# server.py
from fastmcp import FastMCP
import os

# Inicjalizacja serwera
mcp = FastMCP("Mój Serwer Lokalny")

@mcp.tool()
def oblicz_sume(a: int, b: int) -> int:
    """
    Dodaje dwie liczby całkowite. Użyj tego do prostych obliczeń.

    :param a: Pierwsza liczba
    :param b: Druga liczba
    :return: Suma liczb
    """

    return a + b

@mcp.tool()
def greeting(name: str) -> str:
    """
    Wysyła powitanie do użytkownika.

    :param name: Imię użytkownika
    :return: Powitanie
    """
    return f"Cześć {name}!"

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")


def ensure_file():
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding='utf-8') as f:
            f.write("")

@mcp.tool()
def add_note(message: str) -> str:
    """
    Zapisuje notatkę użytkownika do pliku tekstowego.

    Użyj tego narzędzia, gdy użytkownik chce coś zapamiętać lub zapisać na później.

    :param message: Treść notatki do zapisania
    :return: Potwierdzenie zapisania notatki
    """

    ensure_file()
    with open(NOTES_FILE, "a", encoding='utf-8') as f:
        f.write(message + "\n")
    return "Note saved!"


@mcp.tool()
def read_notes() -> str:
    """
    Odczytuje całą zawartość pliku z notatkami.

    Użyj tego narzędzia, gdy chcesz wiedzieć, co użytkownik zapisał wcześniej.

    :return: Pełna treść notatek
    """
    ensure_file()
    with open(NOTES_FILE, "r", encoding='utf-8') as f:
        content = f.read().strip()
    return content or "No notes yet."


@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """
    Pobiera tylko ostatnią dodaną notatkę.

    Przydatne, gdy interesuje Cię tylko najnowszy wpis.

    :return: Treść ostatniej notatki
    """

    ensure_file()
    with open(NOTES_FILE, "r", encoding='utf-8') as f:
        lines = f.readlines()
    return lines[-1].strip() if lines else "No notes yet."


@mcp.prompt()
def note_summary_prompt() -> str:
    """
    Generuje prompt dla modelu, proszący o podsumowanie wszystkich notatek.

    :return: Prompt z treścią notatek
    """

    ensure_file()
    with open(NOTES_FILE, "r", encoding='utf-8') as f:
        content = f.read().strip()
    if not content:
        return "There are no notes yet."
    return f"Summarize the current notes: {content}"



if __name__ == "__main__":
    mcp.run()
