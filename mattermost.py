from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, psycopg2, json, re, logging
from pythonjsonlogger import jsonlogger

def _validate_config() -> None:
    required = ['DB_PASS', 'ID_TOKEN', 'PPPOE_TOKEN']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        missing_str = ', '.join(missing)
        raise EnvironmentError(
            f"Brak wymaganych zmiennych środowiskowych: {missing_str}\n"
            f"Skopiuj .env.example do .env i uzupełnij wartości."
        )

load_dotenv(override=True)
_validate_config()

app = Flask(__name__)

ID_TOKEN = os.getenv("ID_TOKEN")
PPPOE_TOKEN = os.getenv("PPPOE_TOKEN")
FLASK_PORT = os.getenv("FLASK_PORT", 5000)
FLASK_DEBUG = os.getenv("FLASK_DEBUG", False)
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

def setup_logging():
    log_format_env = os.getenv("LOG_FORMAT", "text").strip().lower()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler()

    if log_format_env == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger('mattermost-bot')

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


def _get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS"),
        connect_timeout=10
    )


def _parse_request() -> tuple[dict, str]:
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.values
    return data, data.get('text', '').strip()


def _validate_token(data: dict, env_key: str) -> str | None:
    expected = os.getenv(env_key)
    if not expected:
        return f"Błąd konfiguracji: brak {env_key} w .env"
    if data.get('token') != expected:
        return "Błąd autoryzacji: nieprawidłowy token"
    return None


def set_search_path(cur, schema: str) -> None:
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema):
        raise ValueError(f"Nieprawidłowa nazwa schematu: {schema!r}")
    cur.execute(f'SET search_path TO "{schema}", public')



@app.route('/query/id', methods=['POST'])
def query_id():
    data, text = _parse_request()
    query_id = text.split()[0] if text else None

    logger.info('[/id] Otrzymano zapytanie')

    if not query_id:
        logger.warning('[/id] Brak client_id w zapytaniu')
        return jsonify({"response_type": "ephemeral", "text": "Błąd: Musisz podać client_id. Użycie: /id <client_id>"}), 200

    auth_error = _validate_token(data, "ID_TOKEN")
    if auth_error:
        logger.warning('[/id] Nieudana autoryzacja - nieprawidłowy token')
        return jsonify({"response_type": "ephemeral", "text": auth_error}), 200

    logger.info(f"[/id] Zapytanie o client_id={query_id}")

    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            set_search_path(cur, DB_SCHEMA)
            conn.commit()

        query = f"SELECT client FROM {DB_SCHEMA}.clients WHERE client_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (query_id,))
            rows = cur.fetchall()

        if not rows:
            logger.info(f"[/id] Nie znaleziono klienta: client_id={query_id}")
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
                        "description": flat_dict.get("description") or flat_dict.get("client.description"),
                        "description": flat_dict.get("description") or flat_dict.get("client.description"),
                        "description": flat_dict.get("description") or flat_dict.get("client.description"),
                        "description": flat_dict.get("description") or flat_dict.get("client.description"),
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
                    final_data = {k: v for k, v in filtered_data.items() if v is not None}
                    client_val = json.dumps(final_data, indent=4, ensure_ascii=False)
                    logger.info(f'[/id] Zwrócono dane dla client_id={query_id}')
                else:
                    client_val = json.dumps(parsed, indent=4, ensure_ascii=False)
                    logger.info(f'[/id] Zwrócono dane dla client_id={query_id}')
            except Exception:
                client_val = str(raw_data)
                logger.info(f'[/id] Zwrócono dane dla client_id={query_id}')
        else:
            logger.info(f'[/id] Zwrócono brak danych dla client_id={query_id}')
            client_val = "Brak danych"


        return jsonify({
            "response_type": "in_channel",
            "text": f"**Wynik zapytania dla client_id = {query_id}:**\n```json\n{client_val}\n```",
            "data": {"client": client_val}
        })
    except psycopg2.Error as e:
        logger.error(f"[/id] Błąd bazy danych: {e}", exc_info=True)
        return jsonify({"response_type": "ephemeral", "text": f"Błąd bazy danych: {str(e)}"}), 200
    except Exception as e:
        logger.error(f"[/id] Wewnętrzny błąd serwera: {e}", exc_info=True)
        return jsonify({"response_type": "ephemeral", "text": f"Wewnętrzny błąd serwera: {str(e)}"}), 200


@app.route('/query/pppoe', methods=['POST'])
def query_pppoe():
    data, text = _parse_request()
    query_id = text.split()[0] if text else None

    logger.info('[/pppoe] Otrzymano zapytanie')

    if not query_id:
        logger.warning('[/pppoe] Brak client_id w zapytaniu')
        return jsonify({"response_type": "ephemeral", "text": "Błąd: Musisz podać client_id. Użycie: /pppoe <client_id>"}), 200

    auth_error = _validate_token(data, "PPPOE_TOKEN")
    if auth_error:
        logger.warning('[/pppoe] Nieudana autoryzacja - nieprawidłowy token')
        return jsonify({"response_type": "ephemeral", "text": auth_error}), 200

    logger.info(f"[/pppoe] Zapytanie o pppoe dla client_id={query_id}")

    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            set_search_path(cur, DB_SCHEMA)
            conn.commit()

        query = f"SELECT ip FROM {DB_SCHEMA}.hardware_ips WHERE client_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (query_id,))
            rows = cur.fetchall()


        if not rows:
            logger.info(f"[/pppoe] Nie znaleziono pppoe dla client_id={query_id}")
            return jsonify({"response_type": "ephemeral", "text": f"Nie znaleziono pppoe dla client_id = {query_id}"}), 200

        parsed_results = []
        for row in rows:
            raw_data = row[0]
            if raw_data:
                try:
                    parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    parsed_results.append(parsed)
                    logger.info(f"[/pppoe] Zwrócono dane dla client_id={query_id}")
                except Exception:
                    logger.info(f"[/pppoe] Zwrócono dane dla client_id={query_id}")
                    parsed_results.append(str(raw_data))
            else:
                logger.info(f"[/pppoe] Brak danych o pppoe dla client_id={query_id}")
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


    except psycopg2.Error as e:
        logger.error(f"[/pppoe] Błąd bazy danych: {e}", exc_info=True)
        return jsonify({"response_type": "ephemeral", "text": f"Błąd bazy danych: {str(e)}"}), 200
    except Exception as e:
        logger.error(f"[/pppoe] Wewnętrzny błąd serwera: {e}", exc_info=True)
        return jsonify({"response_type": "ephemeral", "text": f"Wewnętrzny błąd serwera: {str(e)}"}), 200


@app.route('/query/search', methods=['POST'])
def search_query():
    data, text = _parse_request()
    phrase = text.split()[0] if text else None

    logger.info('[/search] Otrzymano zapytanie')

    if not phrase:
        logger.warning('[/search] Brak frazy do wyszukania w zapytaniu')
        return jsonify({"response_type": "ephemeral", "text": "Błąd: Musisz podać szukaną frazę. Uzycie: /search <szukana_fraza>"}), 200

    auth_err = _validate_token(data, "SEARCH_TOKEN")

    if auth_err:
        logger.warning('[/search] Nieudana autoryzacja - nieprawidłowy token')
        return jsonify({"response_type": "ephemeral", "text": auth_err}), 200

    logger.info(f"[/search] Zapytanie o frazę: {phrase}")

    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            set_search_path(cur, DB_SCHEMA)
            conn.commit()

        query = f"SELECT ip FROM {DB_SCHEMA}.hardware_ips WHERE client_id = %s;"
        with conn.cursor() as cur:
            cur.execute(query, (query_id,))
            rows = cur.fetchall()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(FLASK_PORT))
