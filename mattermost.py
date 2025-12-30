from flask import Flask, request, jsonify
import requests
import threading
import psycopg2
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Config
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN")

# Database Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None

def get_schema():
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to database."

    schema_str = ""
    try:
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = cur.fetchall()

        for table in tables:
            table_name = table[0]
            schema_str += f"Table: {table_name}\nColumns: "

            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
            columns = cur.fetchall()
            col_list = [f"{col[0]} ({col[1]})" for col in columns]
            schema_str += ", ".join(col_list) + "\n\n"

        cur.close()
        conn.close()
    except Exception as e:
        return f"Error fetching schema: {e}"

    return schema_str

def execute_read_only_query(query):
    if "drop" in query.lower() or "delete" in query.lower() or "update" in query.lower() or "insert" in query.lower():
        return "Error: I am only allowed to execute SELECT queries."

    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to database."

    try:
        cur = conn.cursor()
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        results = cur.fetchall()

        data = []
        for row in results:
            data.append(dict(zip(columns, row)))

        cur.close()
        conn.close()
        return json.dumps(data, default=str)
    except Exception as e:
        return f"SQL Error: {e}"

def generate_ollama_response(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Error: No response from Ollama")
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

def classify_intent(user_text):
    """Decides if the question is about Database (SQL) or General Chat."""
    prompt = f"""
    Analyze the following user text: "{user_text}"
    Does this text require querying a database to answer?

    - YES if it asks for counts, lists, data from tables, specific records, statistics, or status of items.
    - NO if it is a greeting (hello, hi), a general knowledge question (why is sky blue?), a formatting request, or a joke.

    Answer ONLY with "YES" or "NO". Do not add any punctuation or extra text.
    """
    response = generate_ollama_response(prompt).strip().upper()
    print(f"Intent Classification for '{user_text}': {response}")
    return "YES" in response

def generate_and_reply(user_text, response_url):

    # Step 1: Classify Intent
    is_db_question = classify_intent(user_text)

    if is_db_question:
        # DB FLOW
        schema = get_schema()

        sql_prompt = f"""
        You are a PostgreSQL expert.
        Here is the database schema:
        {schema}

        User Question: {user_text}

        Return ONLY a valid SQL SELECT query to answer the question.
        Do not explain. Do not use markdown code blocks. Just the raw SQL.
        """

        print("Generating SQL...")
        generated_sql = generate_ollama_response(sql_prompt).strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        print(f"Generated SQL: {generated_sql}")

        query_result = execute_read_only_query(generated_sql)
        print(f"Query Result: {query_result}")

        final_prompt = f"""
        User Question: {user_text}
        SQL Query executed: {generated_sql}
        Data Results: {query_result}

        Please answer the user's question in natural language based on the data results.
        """
        final_answer = generate_ollama_response(final_prompt)

        # Add visual indicator
        final_answer = f"**TRYB SQL**\n*Query:* `{generated_sql}`\n\n{final_answer}"

    else:
        # CHAT FLOW
        print("Handling as General Chat...")
        chat_prompt = f"User says: {user_text}\nReply helpfully and concisely."
        final_answer = generate_ollama_response(chat_prompt)

        # Add visual indicator
        final_answer = f"**TRYB CZAT**\n\n{final_answer}"

    payload = {
        "text": final_answer,
        "response_type": "in_channel"
    }
    try:
        requests.post(response_url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Error sending Async response: {e}")

@app.route('/', methods=['POST'])
def mm_webhook():
    data = request.form

    token = data.get('token')
    if token != MATTERMOST_TOKEN:
        return "Unauthorized", 401

    user_text = data.get('text')
    username = data.get('user_name', 'User')
    response_url = data.get('response_url')

    if not user_text:
        return jsonify({
            "text": "Wygląda na to, że Twoja wiadomość jest pusta."
        })

    if username == "ollama-bot":
        return jsonify({})

    if response_url:
        thread = threading.Thread(target=generate_and_reply, args=(user_text, response_url))
        thread.start()

        return jsonify({
            "response_type": "in_channel",
            "text": f"Twoje pytanie: {user_text}\nPrzetwarzam zapytanie..."
        })

    return jsonify({
        "text": "Proszę używać Slash Command."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
