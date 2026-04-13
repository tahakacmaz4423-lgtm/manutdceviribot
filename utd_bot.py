import os
import time
import requests

TELEGRAM_TOKEN = "8698383392:AAEfcHcJvYgpjbgaQnaDGhd52gHuYC494Nw"
CHAT_ID = "5196783255"
RAPIDAPI_KEY = "53e0f8c110msh7f4f7ea23ea96e7p155cc3jsn0e31b8dcb9d3"
TARGET_ACCOUNT = "utdtruthful"
CHECK_INTERVAL = 1800
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

seen_ids = set()

def send_telegram(text, tweet_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🐦 X'te Paylaş", "url": f"https://twitter.com/intent/tweet?text={requests.utils.quote(text[:280])}"},
                {"text": "📎 Orijinal", "url": tweet_url}
            ]]
        }
    }
    r = requests.post(url, json=payload)
    return r.ok

def get_user_id(username):
    r = requests.get(
        f"https://twitter135.p.rapidapi.com/v1.1/GetUserByScreenName/?username={username}",
        headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "twitter135.p.rapidapi.com"}
    )
    return r.json().get("rest_id") or r.json().get("id_str")

def get_tweets(user_id):
    r = requests.get(
        f"https://twitter135.p.rapidapi.com/v1.1/UserTweets/?userId={user_id}&count=10",
        headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "twitter135.p.rapidapi.com"}
    )
    data = r.json()
    entries = []
    try:
        for inst in data["timeline"]["instructions"]:
            for entry in inst.get("entries", []):
                legacy = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {}).get("legacy", {})
                if legacy.get("full_text") and not legacy["full_text"].startswith("RT @"):
                    entries.append({
                        "id": legacy.get("id_str"),
                        "text": legacy.get("full_text"),
                        "url": f"https://twitter.com/{TARGET_ACCOUNT}/status/{legacy.get('id_str')}"
                    })
    except:
        pass
    return entries

def translate(text):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"content-type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300, "messages": [{"role": "user", "content": f"Bu futbol tweetini Türkçeye çevir, sadece çeviriyi yaz:\n{text}"}]}
    )
    return r.json()["content"][0]["text"].strip()

def main():
    print("Bot başladı")
    send_telegram("✅ Bot aktif! @utdtruthful takip ediliyor.", "https://twitter.com/utdtruthful")
    user_id = get_user_id(TARGET_ACCOUNT)
    print(f"User ID: {user_id}")
    for t in get_tweets(user_id):
        seen_ids.add(t["id"])
    while True:
        try:
            for tweet in reversed(get_tweets(user_id)):
                if tweet["id"] not in seen_ids:
                    seen_ids.add(tweet["id"])
                    tr = translate(tweet["text"])
                    send_telegram(f"🔴 <b>@utdtruthful</b>\n\n{tr}", tweet["url"])
                    time.sleep(3)
        except Exception as e:
            print(f"Hata: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
