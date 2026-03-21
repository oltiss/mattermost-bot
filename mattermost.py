from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, requests, asyncio, psycopg2, threading, json
from ai_handler import process_query
from slash_commands import slash_coms

load_dotenv()

app = Flask(__name__)

SQL_TOKEN = os.getenv("SQL_TOKEN")
ID_TOKEN = os.getenv("ID_TOKEN")
PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")
FLASK_PORT = os.getenv("FLASK_PORT", 5000)

def handle_background_processing(prompt, response_url):
    """
    Runs the async process_query in a background thread and sends the result to Mattermost.
    """
    try:
        # Run the async function
        result_text = asyncio.run(process_query(prompt))

        # Prepare response for Mattermost
        payload = {
            "response_type": "in_channel",
            "text": result_text
        }

        # Send delayed response
        print(f"📤 Wysyłanie odpowiedzi do: {response_url}")
        resp = requests.post(response_url, json=payload)
        print(f"✅ Status wysyłki Mattermost: {resp.status_code}, Treść: {resp.text}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Send error message if something fails
        error_payload = {
            "response_type": "ephemeral",
            "text": f"Error processing request: {str(e)}"
        }
        try:
            requests.post(response_url, json=error_payload)
        except:
            print("Failed to send error message to Mattermost.")


@app.route('/', methods=['POST'])
def mm_webhook():
    data = request.form
    token = data.get('token')
    text = data.get('text', '')
    response_url = data.get('response_url')
    user_name = data.get('user_name', 'User')

    if not text:
         return jsonify({
            "response_type": "ephemeral",
            "text": "Please provide a query."
        })

    if not response_url:
        return jsonify({
            "response_type": "ephemeral",
            "text": "Missing response_url. This command must be run from Mattermost."
        })

    system_instruction = slash_coms(token, text)
    if system_instruction is not None:
        prompt = system_instruction
    else:
        return jsonify({"text": "Invalid token"}), 401



    # Start background processing
    thread = threading.Thread(target=handle_background_processing, args=(prompt, response_url))
    thread.start()

    # Return immediate acknowledgement
    return jsonify({
        "response_type": "in_channel",
        "text": f"🧠 Thinking... (Query: {text})"
    })


@app.route('/query', methods=['GET', 'POST'])
def query_endpoint():
    """
    Centralny endpoint dla slash commands: /id i /pppoe
    Rozpoznaje komendę i wykonuje odpowiednie zapytanie SQL
    """
    from dotenv import load_dotenv
    from psycopg2 import Error

    load_dotenv()

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS")
    DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
    ID_TOKEN = os.getenv("ID_TOKEN")
    PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")

    # Pobieranie danych z wykorzystaniem request.values (obsługuje GET args i POST form)
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.values

    data_text = data.get('text', '')
    req_command = data.get('command', '')
    provided_token = data.get('token')

    if req_command:
        command = req_command.strip().lstrip('/').lower()
        query_id = data_text.strip().split()[0] if data_text.strip() else None
    else:
        data_text_stripped = data_text.strip()
        command = data_text_stripped.split()[0].lstrip('/').lower() if data_text_stripped.startswith('/') else None
        query_id = data_text_stripped.split()[1] if len(data_text_stripped.split()) > 1 else None

    # Sprawdź czy komenda istnieje
    if not command:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Błąd: Nie udało się odczytać komendy z żądania. Przysłano command='{req_command}', text='{data_text}'"
        }), 200

    # Walidacja tokena
    token_map = {
        'id': ID_TOKEN,
        'pppoe': PPPOE_TOKEN
    }

    if command not in token_map:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Błąd: Nieznana komenda '{command}'. Obsługiwane komendy to /id lub /pppoe."
        }), 200

    expected_token = token_map.get(command)

    if not expected_token:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Błąd konfiguracji bota: Brak tokenu w pliku .env dla komendy '{command}'. Upewnij się, że zmienna ID_TOKEN (lub PPPOE_TOKEN) jest prawidłowo ustawiona i zrestartuj serwer."
        }), 200

    if not provided_token or provided_token != expected_token:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Błąd autoryzacji: Nieprawidłowy token dla komendy /{command}."
        }), 200

    # Budowanie zapytania SQL w zależności od komendy
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=10
        )

        # Ustawienie sesji na read-only
        with conn.cursor() as cur:
            cur.execute("SET search_path TO " + DB_SCHEMA + ", public")
            conn.commit()
            cur.close()

        if command == 'id':
            # Zapytanie do tabeli clients
            query = f"""
                SELECT client
                FROM {DB_SCHEMA}.clients
                WHERE client_id = %s;
            """
            with conn.cursor() as cur:
                cur.execute(query, (query_id,))
                rows = cur.fetchall()

            conn.close()

            if rows:
                raw_data = rows[0][0]
                if raw_data:
                    try:
                        parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        client_val = json.dumps(parsed, indent=4, ensure_ascii=False)
                    except Exception:
                        client_val = str(raw_data)
                else:
                    client_val = "Brak danych"
                return jsonify({
                    "response_type": "in_channel",
                    "text": f"**Wynik zapytania dla client_id = {query_id}:**\n```json\n{client_val}\n```",
                    "data": {
                        "client": client_val
                    }
                })
            else:
                return jsonify({
                    "response_type": "ephemeral",
                    "text": f"Nie znaleziono klienta o client_id = {query_id}"
                }), 200

        elif command == 'pppoe':
            # Zapytanie do tabeli hardware_ips
            query = f"""
                SELECT ip
                FROM {DB_SCHEMA}.hardware_ips
                WHERE client_id = %s;
            """
            with conn.cursor() as cur:
                cur.execute(query, (query_id,))
                rows = cur.fetchall()

            conn.close()

            if rows:
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

                # Zwróć jako jeden JSON, jeśli jest to jeden rekord, lub jako listę JSON-ów (Array), jeśli jest ich więcej
                final_data = parsed_results[0] if len(parsed_results) == 1 else parsed_results
                ip_val = json.dumps(final_data, indent=4, ensure_ascii=False)

                return jsonify({
                    "response_type": "in_channel",
                    "text": f"**Znaleziono {len(rows)} rekord(ów) dla client_id = {query_id}:**\n```json\n{ip_val}\n```",
                    "data": {
                        "ip": ip_val
                    }
                })
            else:
                return jsonify({
                    "response_type": "ephemeral",
                    "text": f"Nie znaleziono pppoe dla client_id = {query_id}"
                }), 200

        else:
            return jsonify({
                "response_type": "ephemeral",
                "text": "Błąd wewnętrzny: Przekazano nieznaną komendę."
            }), 200

    except Error as e:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Błąd bazy danych: {str(e)}"
        }), 200

    except Exception as e:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Wewnętrzny błąd serwera: {str(e)}"
        }), 200




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(FLASK_PORT), debug=True)
