import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TELEGRAM_TOKEN = "8698383392:AAEfcHcJvYgpjbgaQnaDGhd52gHuYC494Nw"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def translate(text):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "content-type": "application/json",
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": f"Bu futbol tweetini Türkçeye çevir, sadece çeviriyi yaz:\n{text}"}]
        }
    )
    return r.json()["content"][0]["text"].strip()

def send_message(chat_id, text, tweet_text=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if tweet_text:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🐦 X'te Paylaş", "url": f"https://twitter.com/intent/tweet?text={requests.utils.quote(tweet_text[:280])}"}
            ]]
        }
    requests.post(url, json=payload)

def process_update(update):
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if not text or not chat_id:
        return
    if text == "/start":
        send_message(chat_id, "👋 Merhaba! İngilizce tweeti yapıştır, Türkçeye çevireyim ve paylaşım butonunu hazırlayayım!")
        return
    send_message(chat_id, "⏳ Çevriliyor...")
    try:
        turkish = translate(text)
        send_message(chat_id, f"✅ <b>Türkçe:</b>\n\n{turkish}", turkish)
    except Exception as e:
        send_message(chat_id, "❌ Hata, tekrar dene.")
        print(f"Hata: {e}")

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        self.send_response(200)
        self.end_headers()
        try:
            process_update(json.loads(body))
        except Exception as e:
            print(e)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Calisiyor!")

    def log_message(self, *args):
        pass

def main():
    port = int(os.environ.get("PORT", 10000))
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if render_url:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            json={"url": f"{render_url}"}
        )
        print(f"Webhook kuruldu: {render_url}")
    print(f"Bot başladı port {port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

if __name__ == "__main__":
    main()
