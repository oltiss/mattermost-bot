from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

API_KEY = "AIzaSyBMmCVJ8HMgjqr7ScGBMhsvLG3ireIaCo8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat()

MATTERMOST_TOKEN = "uo4a1o5yc3ffd891p5pd13pe8y"


@app.route('/', methods=['POST'])
def mm_webhook():
    data = request.form

    token = data.get('token')
    if token != MATTERMOST_TOKEN:
        return "Unauthorized", 401
    
    user_text = data.get('text')

    if not user_text:
        return jsonify({
            "text": "Wygląda na to, że Twoja wiadomość jest pusta.",
            "icon_url": "http://109.95.202.14:4000"
        })

    response = chat.send_message(user_text)

    return jsonify({
        "text": response.text,
        "icon_url": "http://109.95.202.14:4000"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)