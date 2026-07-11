import os, logging, json, time
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = "8748341489:AAEMVivrhW0-4H8wG1osngHNRWJfIaT5laM"
ADMIN_CHAT_ID = None
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
LEADS_FILE = "/tmp/leads.json"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ─── LEAD DATABASE ───
def load_leads():
    try:
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_leads(leads):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f)

def track_lead(chat_id, interest, name="User"):
    leads = load_leads()
    uid = str(chat_id)
    now = int(time.time())
    if uid not in leads:
        leads[uid] = {"chat_id": chat_id, "name": name, "interest": interest, "first_seen": now, "last_interaction": now, "followup_stage": 0, "followup_sent_at": [], "opted_out": False}
    else:
        leads[uid]["last_interaction"] = now
        leads[uid]["interest"] = interest
        if leads[uid].get("opted_out"):
            leads[uid]["opted_out"] = False
            leads[uid]["followup_stage"] = 0
    save_leads(leads)

# ─── FOLLOW-UP SEQUENCE ───
FOLLOWUPS = [
    {"stage": 1, "delay_hours": 24,
     "text": "Hi again! 👋 Still thinking about the course?\n\nHere's what our students say:\n\"I was sceptical at first, but after 30 days I was consistently profitable. Best investment I ever made.\" — Ahmad R.\n\n📅 Next KL intake is filling fast. Only 50 seats.\n\n👉 Register: https://whatsform.com/ghwpgv",
     "button": {"text": "📝 Register Now", "url": "https://whatsform.com/ghwpgv"}},
    {"stage": 2, "delay_hours": 72,
     "text": "Hey! Just a heads up — **only 12 seats left** for the upcoming KL intake. 🚀\n\n1,200+ students already transformed their trading. Don't miss your chance.\n\n👉 Secure your seat now: https://whatsform.com/ghwpgv\n\nOr ask me anything — I'm here to help!",
     "button": {"text": "💬 Ask Hafizzat", "url": "https://wa.me/60133355669"}},
    {"stage": 3, "delay_hours": 168,
     "text": "⚠️ *Last Call!*\n\nThis is your final reminder — seats for the upcoming Turn Charts Into Cashflow intake are almost gone.\n\nAfter this, next intake date is TBD.\n\nDon't let this opportunity slip. Join 1,200+ successful traders today.\n\n👉 https://whatsform.com/ghwpgv",
     "button": {"text": "🚀 Register Now", "url": "https://whatsform.com/ghwpgv"}}
]

def process_followups():
    leads = load_leads()
    now = int(time.time())
    sent = 0
    for uid, lead in leads.items():
        if lead.get("opted_out"): continue
        current_stage = lead.get("followup_stage", 0)
        if current_stage >= len(FOLLOWUPS): continue
        fu = FOLLOWUPS[current_stage]
        if (now - lead.get("first_seen", now)) >= fu["delay_hours"] * 3600:
            buttons = {"inline_keyboard": [[fu["button"], {"text": "⏹ Stop Updates", "callback_data": f"optout_{uid}"}]]}
            try:
                send_msg(lead["chat_id"], fu["text"], reply_markup=buttons)
                leads[uid]["followup_stage"] = current_stage + 1
                leads[uid]["followup_sent_at"].append(int(time.time()))
                sent += 1
            except Exception as e:
                logging.error(f"Follow-up failed for {uid}: {e}")
    save_leads(leads)
    return sent

# ─── KEYBOARDS ───
def main_menu():
    return {"inline_keyboard": [
        [{"text": "🤖 HR AI - Trading Systems", "callback_data": "hr_ai"}],
        [{"text": "📚 Turn Charts Into Cashflow", "callback_data": "course"}],
        [{"text": "💰 Pricing", "callback_data": "pricing"}],
        [{"text": "📞 Contact / WhatsApp", "callback_data": "contact"}],
        [{"text": "🎥 YouTube Channel", "url": "https://youtube.com/@HafizzatRusli"}]
    ]}

def back_button():
    return {"inline_keyboard": [[{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]]}

def pricing_buttons():
    return {"inline_keyboard": [
        [{"text": "💬 Ask About HR AI", "callback_data": "contact"}],
        [{"text": "📚 Ask About Course", "callback_data": "course_contact"}],
        [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]
    ]}

# ─── MESSAGES ───
WELCOME = "👋 *Assalamualaikum & Welcome!*\n\nI'm Lia, Hafizzat Rusli's virtual assistant. How can I help you today?\n\n👇 Choose an option below:"
HR_AI_MSG = "🤖 *HR AI — Automated Trading Systems*\n\nBuilt for serious traders who want *consistent, automated execution* on MT5.\n\n✅ Delta-neutral strategies\n✅ Quant-tested & validated\n✅ FxPro compatible\n✅ 24/7 automated execution\n\n👉 *Self-Serve:* RM28,149\n👉 *Turnkey:* RM45,873\n\nTap Contact below to see live case studies."
COURSE_MSG = "📚 *Turn Charts Into Cashflow*\n\n*Ready to Turn Charts Into Cashflow?*\n\n✅ 1,200+ Students Trained\n✅ 87% Reached Profitability Within 30 Days\n✅ Lifetime Access\n✅ VIP WhatsApp Support Group\n\n⚠️ Only 50 Seats — Next Intake: KL\n\n💎 *Choose Your Path:*\n• Basic — RM5,000\n• Intermediate — RM10,000\n• Advanced — RM20,000\n• Ultimate — RM40,000\n• ♾️ Infinite — RM80,000\n\n👇 Register below!"
PRICING_MSG = "💰 *Pricing*\n\n━━━━━━━━━━━━━━━━━\n🤖 *HR AI Trading Systems*\n• Self-Serve: RM28,149\n• Turnkey: RM45,873\n\n📚 *Turn Charts Into Cashflow*\n• Basic: RM5,000\n• Intermediate: RM10,000\n• Advanced: RM20,000\n• Ultimate: RM40,000\n• Infinite: RM80,000\n\n💳 *Payment:* BTC / USDT / USDC"
CONTACT_MSG = "📞 *Contact Hafizzat Rusli*\n\n💬 *WhatsApp:* wa.me/60133355669\n📱 *Telegram:* @MsRinaC\n📧 *IG/FB:* @hafizzatrusli\n🎥 *YouTube:* @HafizzatRusli"
COURSE_CONTACT_MSG = "📚 *Course Registration*\n\nReady to join?\n\n📱 Register: https://whatsform.com/ghwpgv\n💬 Our team will WhatsApp you to reserve your seat!\n\n📞 Or WhatsApp: wa.me/60133355669"

def send_msg(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    try: return requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10).json()
    except: return None

def answer_cbq(cid, text):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": cid, "text": text, "show_alert": False}, timeout=5)

def edit_msg(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)

def notify_admin(text):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID: send_msg(ADMIN_CHAT_ID, f"📬 *New Lead*\n\n{text}")

def handle_start(chat_id):
    send_msg(chat_id, WELCOME, reply_markup=main_menu())
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID is None:
        ADMIN_CHAT_ID = chat_id
        send_msg(chat_id, "✅ You're now admin. You'll receive lead notifications.")
    track_lead(chat_id, "started")

def handle_callback(chat_id, message_id, data, cb_id):
    if data.startswith("optout_"):
        uid = data.replace("optout_", "")
        leads = load_leads()
        if uid in leads: leads[uid]["opted_out"] = True; save_leads(leads)
        answer_cbq(cb_id, "Unsubscribed ✅")
        edit_msg(chat_id, message_id, "You've been unsubscribed from follow-ups ✅\n\nMenu still available!", reply_markup=main_menu())
        return
    actions = {"main_menu": (WELCOME, main_menu()), "hr_ai": (HR_AI_MSG, back_button()), "course": (COURSE_MSG, back_button()), "pricing": (PRICING_MSG, pricing_buttons())}
    if data in actions:
        text, kb = actions[data]; edit_msg(chat_id, message_id, text, reply_markup=kb); answer_cbq(cb_id, "Loading...")
        track_lead(chat_id, data)
        if data in ("hr_ai", "course"): notify_admin(f"👤 Someone viewed *{data.replace('_',' ').title()}* info")
    elif data == "contact":
        edit_msg(chat_id, message_id, CONTACT_MSG, reply_markup={"inline_keyboard": [[{"text": "💬 WhatsApp Now", "url": "https://wa.me/60133355669"}], [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]]})
        answer_cbq(cb_id, "Contact"); track_lead(chat_id, "contact"); notify_admin("👤 Someone requested *Contact* — potential lead!")
    elif data == "course_contact":
        edit_msg(chat_id, message_id, COURSE_CONTACT_MSG, reply_markup={"inline_keyboard": [[{"text": "📱 Register Now", "url": "https://whatsform.com/ghwpgv"}], [{"text": "💬 WhatsApp Now", "url": "https://wa.me/60133355669"}], [{"text": "⬅️ Back to Menu", "callback_data": "main_menu"}]]})
        answer_cbq(cb_id, "Course contact"); track_lead(chat_id, "course_contact"); notify_admin("👤 Someone wants to *join the course*!")

def handle_message(chat_id, text):
    global ADMIN_CHAT_ID
    track_lead(chat_id, f"msg: {text[:50]}")
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
            cb = update["callback_query"]; cid = cb.get("message",{}).get("chat",{}).get("id"); mid = cb.get("message",{}).get("message_id"); data = cb.get("data",""); cbid = cb.get("id")
            if data: handle_callback(cid, mid, data, cbid)
        elif "message" in update:
            msg = update["message"]; cid = msg.get("chat",{}).get("id"); text = msg.get("text","")
            if text == "/start": handle_start(cid)
            else: handle_message(cid, text)
    except Exception as e: logging.error(f"Error: {e}")
    return jsonify({"ok": True})

@app.route("/cron", methods=["GET"])
def cron():
    sent = process_followups()
    leads = load_leads()
    return jsonify({"status": "ok", "followups_sent": sent, "total_leads": len(leads), "active_leads": sum(1 for l in leads.values() if not l.get("opted_out"))})

@app.route("/leads", methods=["GET"])
def leads_report():
    leads = load_leads(); total = len(leads); active = sum(1 for l in leads.values() if not l.get("opted_out"))
    s = {1:0,2:0,3:0}
    for l in leads.values():
        st = l.get("followup_stage",0)
        if st in s: s[st] += 1
    return jsonify({"total":total,"active":active,"opted_out":total-active,"stage1":s[1],"stage2":s[2],"stage3":s[3]})

def set_webhook():
    url = os.environ.get("PUBLIC_URL", "")
    if url:
        r = requests.get(f"{BASE_URL}/setWebhook?url={url}/webhook")
        logging.info(f"Webhook: {r.json()}")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
