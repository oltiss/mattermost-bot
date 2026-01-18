from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import threading
import asyncio
from ai_handler import process_query

load_dotenv()

app = Flask(__name__)

MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN")
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

    # Verify the token from Mattermost
    if MATTERMOST_TOKEN and token != MATTERMOST_TOKEN:
        return jsonify({"text": "Invalid token"}), 401

    user_name = data.get('user_name', 'User')
    text = data.get('text', '')
    response_url = data.get('response_url')

    if not text:
         return jsonify({
            "response_type": "ephemeral",
            "text": "Please provide a query."
        })

    # Start background processing
    thread = threading.Thread(target=handle_background_processing, args=(text, response_url))
    thread.start()

    # Return immediate acknowledgement
    return jsonify({
        "response_type": "in_channel",
        "text": f"🧠 Thinking... (Query: {text})"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(FLASK_PORT))
