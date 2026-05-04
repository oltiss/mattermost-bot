from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, requests, asyncio, psycopg2, threading, json

load_dotenv(override=True)

app = Flask(__name__)

SQL_TOKEN = os.getenv("SQL_TOKEN")
ID_TOKEN = os.getenv("ID_TOKEN")
PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")
FLASK_PORT = os.getenv("FLASK_PORT", 5000)

def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if isinstance(x, dict):
            if not x:
                if name: out[name[:-1]] = {}
                return
            for key in x:
                flatten(x[key], name + str(key) + '.')
        elif isinstance(x, list):
            if not x:
                if name: out[name[:-1]] = []
                return
            for i, item in enumerate(x):
                flatten(item, name + str(i) + '.')
        else:
            if name:
                out[name[:-1]] = x

    flatten(y)
    if not out and isinstance(y, (dict, list)):
        return y
    return out



@app.route('/query/id', methods=['POST'])
def query_id():
    """
    Endpoint dla slash command: /id
    Wykonuje zapytanie o dane klienta na podstawie client_id.
    """
    from dotenv import load_dotenv
    from psycopg2 import Error

    load_dotenv(override=True)

    DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_SCHEMA = (
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_NAME", "postgres"),
        os.getenv("DB_USER", "postgres"),
        os.getenv("DB_PASS"),
        os.getenv("DB_SCHEMA", "public"),
    )
    ID_TOKEN = os.getenv("ID_TOKEN")

    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.values

    data_text = data.get('text', '')
    provided_token = data.get('token')
    query_id = data_text.strip().split()[0] if data_text.strip() else None

    if not query_id:
        return jsonify({"response_type": "ephemeral", "text": "Błąd: Musisz podać client_id. Użycie: /id <client_id>"}), 200

    if not ID_TOKEN:
        return jsonify({"response_type": "ephemeral", "text": "Błąd konfiguracji bota: Brak tokenu ID_TOKEN w pliku .env."}), 200

    if not provided_token or provided_token != ID_TOKEN:
        return jsonify({"response_type": "ephemeral", "text": "Błąd autoryzacji: Nieprawidłowy token dla komendy /id."}), 200

    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO " + DB_SCHEMA + ", public")
            conn.commit()

        query = f"SELECT client FROM {DB_SCHEMA}.clients WHERE client_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (query_id,))
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return jsonify({"response_type": "ephemeral", "text": f"Nie znaleziono klienta o client_id = {query_id}"}), 200

        raw_data = rows[0][0]
        if raw_data:
            try:
                parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                if isinstance(parsed, (dict, list)):
                    flat_dict = flatten_json(parsed)
                    filtered_data = {
                        "name": flat_dict.get("name") or flat_dict.get("client.name"),
                        "status": flat_dict.get("status") or flat_dict.get("client.status"),
                        "typ": flat_dict.get("typ") or flat_dict.get("client.typ"),
                        "description": flat_dict.get("desciption") or flat_dict.get("client.description"),
                        "iban": flat_dict.get("iban") or flat_dict.get("client.iban"),
                        "email": flat_dict.get("email") or flat_dict.get("customer.email.0"),
                        "phoneNumber": flat_dict.get("phoneNumber") or flat_dict.get("contact.person.0.phoneNumber"),
                        "nip": flat_dict.get("nip") or flat_dict.get("customer.nip"),
                        "address1": flat_dict.get("address1") or flat_dict.get("customer.address.street_1"),
                        "address2": flat_dict.get("address2") or flat_dict.get("customer.address.street_2"),
                        "propertyNumber": flat_dict.get("numberProperty") or flat_dict.get("customer.address.numberProperty"),
                        "klatka": flat_dict.get("numberBlock") or flat_dict.get("customer.address.numberBlock"),
                        "mieszkanie": flat_dict.get("numberApartment") or flat_dict.get("customer.address.numberApartment"),
                        "zipCode": flat_dict.get("zipCode") or flat_dict.get("customer.address.zipCode"),
                        "city": flat_dict.get("city") or flat_dict.get("customer.address.city"),
                        "state": flat_dict.get("state") or flat_dict.get("customer.address.state"),
                    }
                    # Usuwamy klucze, których nie znaleziono (wartość to None)
                    final_data = {k: v for k, v in filtered_data.items() if v is not None}
                    client_val = json.dumps(final_data, indent=4, ensure_ascii=False)
                else:
                    client_val = json.dumps(parsed, indent=4, ensure_ascii=False)
            except Exception:
                client_val = str(raw_data)
        else:
            client_val = "Brak danych"


        return jsonify({
            "response_type": "in_channel",
            "text": f"**Wynik zapytania dla client_id = {query_id}:**\n```json\n{client_val}\n```",
            "data": {"client": client_val}
        })
    except Error as e:
        return jsonify({"response_type": "ephemeral", "text": f"Błąd bazy danych: {str(e)}"}), 200
    except Exception as e:
        return jsonify({"response_type": "ephemeral", "text": f"Wewnętrzny błąd serwera: {str(e)}"}), 200


@app.route('/query/pppoe', methods=['POST'])
def query_pppoe():
    """
    Endpoint dla slash command: /pppoe
    Wykonuje zapytanie o dane pppoe na podstawie client_id.
    """
    from dotenv import load_dotenv
    from psycopg2 import Error

    load_dotenv(override=True)

    DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_SCHEMA = (
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_NAME", "postgres"),
        os.getenv("DB_USER", "postgres"),
        os.getenv("DB_PASS"),
        os.getenv("DB_SCHEMA", "public"),
    )
    PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")

    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.values

    data_text = data.get('text', '')
    provided_token = data.get('token')
    query_id = data_text.strip().split()[0] if data_text.strip() else None

    if not query_id:
        return jsonify({"response_type": "ephemeral", "text": "Błąd: Musisz podać client_id. Użycie: /pppoe <client_id>"}), 200

    if not PPPOE_TOKEN:
        return jsonify({"response_type": "ephemeral", "text": "Błąd konfiguracji bota: Brak tokenu PPPOE_TOKEN w pliku .env."}), 200

    if not provided_token or provided_token != PPPOE_TOKEN:
        return jsonify({"response_type": "ephemeral", "text": "Błąd autoryzacji: Nieprawidłowy token dla komendy /pppoe."}), 200

    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO " + DB_SCHEMA + ", public")
            conn.commit()

        query = f"SELECT ip FROM {DB_SCHEMA}.hardware_ips WHERE client_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (query_id,))
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return jsonify({"response_type": "ephemeral", "text": f"Nie znaleziono pppoe dla client_id = {query_id}"}), 200

        parsed_results = []
        for row in rows:
            raw_data = row[0]
            if raw_data:
                try:
                    parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    parsed_results.append(parsed)
                except Exception:
                    parsed_results.append(str(raw_data))
            else:
                parsed_results.append("Brak danych")

        flat_results = []
        for p in parsed_results:
            if isinstance(p, (dict, list)):
                flat_results.append(flatten_json(p))
            else:
                flat_results.append(p)

        final_data = flat_results[0] if len(flat_results) == 1 else flat_results
        ip_val = json.dumps(final_data, indent=4, ensure_ascii=False)

        return jsonify({
            "response_type": "in_channel",
            "text": f"**Znaleziono {len(rows)} rekord(ów) dla client_id = {query_id}:**\n```json\n{ip_val}\n```",
            "data": {"ip": ip_val}
        })
    except Error as e:
        return jsonify({"response_type": "ephemeral", "text": f"Błąd bazy danych: {str(e)}"}), 200
    except Exception as e:
        return jsonify({"response_type": "ephemeral", "text": f"Wewnętrzny błąd serwera: {str(e)}"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(FLASK_PORT), debug=True)
