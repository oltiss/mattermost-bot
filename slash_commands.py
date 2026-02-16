from dotenv import load_dotenv
from flask import jsonify
import os

load_dotenv()
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
SQL_TOKEN = os.getenv("SQL_TOKEN")
ID_TOKEN = os.getenv("ID_TOKEN")
PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")


def slash_coms(token, id):

    prompt = None

    if token == SQL_TOKEN:
        prompt = ""


    if token == ID_TOKEN:
        prompt = f"""Użytkownik podał ci właśnie klienta o client_id = {id} z tabeli clients,
                     która znajduje się w schemacie {DB_SCHEMA}. Masz na celu znalezienie rekordu
                     z tym id, a następnie z kolumny 'client' pobierz dane. Dane te są zapisane w JSON object.
                     Jako odpowiedź wypisz tylko te dane z odpowiednimi opisami.
                     Jeśli coś jest równe null, false, 0 lub empty string i tak masz to wypisać.
                     Jeśli nie możesz znaleźć rekordu z tym id, poinformuj o tym użytkownika,
                     a nie wymyślaj danych."""



    if token == PPPOE_TOKEN:
        prompt = f"""Użytkownik podał ci właśnie klienta o ip_id = {id} z tabeli hardware_ips,
                     która znajduje się w schemacie {DB_SCHEMA}. Masz na celu znalezienie rekordu
                     z tym id, a następnie z kolumny 'ip' pobierz dane. Dane te są zapisane w JSON object.
                     Jako odpowiedź wypisz tylko te dane z odpowiednimi opisami.
                     Jeśli coś jest równe null, false, 0 lub empty string i tak masz to wypisać.
                     Jeśli nie możesz znaleźć rekordu z tym id, poinformuj o tym użytkownika,
                     a nie wymyślaj danych."""


    return prompt
