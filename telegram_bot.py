import os, logging, json
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = "8748341489:AAEMVivrhW0-4H8wG1osngHNRWJfIaT5laM"
ADMIN_CHAT_ID = None
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🤖 HR AI - Trading Systems", "callback_data": "hr_ai"}],
            [{"text": "📚 Turn Charts Into Cashflow", "callback_data": "course"}],
            [{"text": "💰 Pricing", "callback_data": "pricing"}],
            [{"text": "📞 Contact / WhatsApp", "callback_data": "contact"}],
            [{"text": "🎥 YouTube Channel", "url": "https://youtube.com/@HafizzatRusli"}]
        ]
    }

def back_button():
    return {"inline_keyboard": [[{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]]}

def pricing_buttons():
    return {
        "inline_keyboard": [
            [{"text": "💬 Ask About HR AI", "callback_data": "contact"}],
            [{"text": "📚 Ask About Course", "callback_data": "course_contact"}],
            [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]
        ]
    }

WELCOME = "👋 *Assalamualaikum & Welcome!*\n\nI'm Lia, Hafizzat Rusli's virtual assistant. How can I help you today?\n\n👇 Choose an option below:"

HR_AI_MSG = "🤖 *HR AI — Automated Trading Systems*\n\nBuilt for serious traders who want *consistent, automated execution* on MT5.\n\n✅ Delta-neutral strategies\n✅ Quant-tested & validated\n✅ FxPro compatible\n✅ 24/7 automated execution\n\n👉 *Self-Serve:* RM28,149\n👉 *Turnkey:* RM45,873\n\nTap Contact below to see live case studies."

COURSE_MSG = "📚 *Turn Charts Into Cashflow*\n\n*Ready to Turn Charts Into Cashflow?*\n\n✅ 1,200+ Students Trained\n✅ 87% Reached Profitability Within 30 Days\n✅ Lifetime Access to Course Materials\n✅ Exclusive VIP WhatsApp Support Group\n\n⚠️ Only 50 Seats Available — Next Intake: KL\n\n💎 *Choose Your Path:*\n• Basic — RM5,000\n• Intermediate — RM10,000\n• Advanced — RM20,000\n• Ultimate — RM40,000\n• ♾️ Infinite Access (Best Value) — RM80,000\n\n👇 Register or ask below!"

PRICING_MSG = "💰 *Pricing*\n\n━━━━━━━━━━━━━━━━━\n🤖 *HR AI Trading Systems*\n• Self-Serve: RM28,149\n• Turnkey: RM45,873\n\n📚 *Turn Charts Into Cashflow*\n• Basic: RM5,000\n• Intermediate: RM10,000\n• Advanced: RM20,000\n• Ultimate: RM40,000\n• Infinite: RM80,000\n\n💳 *Payment:* BTC / USDT / USDC\n━━━━━━━━━━━━━━━━━"

CONTACT_MSG = "📞 *Contact Hafizzat Rusli*\n\n💬 *WhatsApp:* wa.me/60133355669\n📱 *Telegram:* @MsRinaC\n📧 *IG/FB:* @hafizzatrusli\n🎥 *YouTube:* @HafizzatRusli"

COURSE_CONTACT_MSG = "📚 *Course Registration*\n\nReady to join Turn Charts Into Cashflow?\n\n📱 Register: https://whatsform.com/ghwpgv\n💬 Once submitted, our team will WhatsApp you to reserve your seat!\n\n📞 Or WhatsApp now: wa.me/60133355669"

def send_msg(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10).json()
    except Exception as e:
        logging.error(f"Send failed: {e}")
        return None

def answer_cbq(callback_query_id, text):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={
        "callback_query_id": callback_query_id, "text": text, "show_alert": False
    }, timeout=5)

def edit_msg(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)

def notify_admin(text):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        send_msg(ADMIN_CHAT_ID, f"📬 *New Lead*\n\n{text}")

def handle_start(chat_id):
    send_msg(chat_id, WELCOME, reply_markup=main_menu())
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID is None:
        ADMIN_CHAT_ID = chat_id
        send_msg(chat_id, "✅ You're now set as admin. You'll receive lead notifications here.")

def handle_callback(chat_id, message_id, data):
    actions = {
        "main_menu": (WELCOME, main_menu()),
        "hr_ai": (HR_AI_MSG, back_button()),
        "course": (COURSE_MSG, back_button()),
        "pricing": (PRICING_MSG, pricing_buttons()),
    }
    if data in actions:
        text, kb = actions[data]
        edit_msg(chat_id, message_id, text, reply_markup=kb)
        answer_cbq(data, "Loading...")
        if data in ("hr_ai", "course"):
            notify_admin(f"👤 Someone viewed *{data.replace('_',' ').title()}* info")
    elif data == "contact":
        edit_msg(chat_id, message_id, CONTACT_MSG, reply_markup={
            "inline_keyboard": [
                [{"text": "💬 WhatsApp Now", "url": "https://wa.me/60133355669"}],
                [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]
            ]
        })
        answer_cbq(data, "Contact")
        notify_admin("👤 Someone requested *Contact* info — potential lead!")
    elif data == "course_contact":
        edit_msg(chat_id, message_id, COURSE_CONTACT_MSG, reply_markup={
            "inline_keyboard": [
                [{"text": "📱 Register Now", "url": "https://whatsform.com/ghwpgv"}],
                [{"text": "💬 WhatsApp Now", "url": "https://wa.me/60133355669"}],
                [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]
            ]
        })
        answer_cbq(data, "Course contact")
        notify_admin("👤 Someone wants to *join the course*!")

def handle_message(chat_id, text):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID and chat_id != ADMIN_CHAT_ID:
        notify_admin(f"📩 *Message from user*\nChat ID: `{chat_id}`\nMessage: _{text}_")
        send_msg(chat_id, "Thanks! Hafizzat will get back to you soon. 🙏\n\nCheck the menu above 👆", reply_markup=main_menu())

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "@Lia_489_bot"})

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    try:
        if "callback_query" in update:
            cb = update["callback_query"]
            msg = cb.get("message", {})
            cid = msg.get("chat", {}).get("id")
            mid = msg.get("message_id")
            data = cb.get("data", "")
            if data:
                answer_cbq(cb.get("id"), "Loading...")
                handle_callback(cid, mid, data)
        elif "message" in update:
            msg = update["message"]
            cid = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            if text == "/start":
                handle_start(cid)
            else:
                handle_message(cid, text)
    except Exception as e:
        logging.error(f"Error: {e}")
    return jsonify({"ok": True})

def set_webhook():
    url = os.environ.get("PUBLIC_URL", "")
    if url:
        r = requests.get(f"{BASE_URL}/setWebhook?url={url}/webhook")
        logging.info(f"Webhook: {r.json()}")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
