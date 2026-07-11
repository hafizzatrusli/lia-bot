import os, logging, json, time
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = "8748341489:AAEMVivrhW0-4H8wG1osngHNRWJfIaT5laM"
ADMIN_CHAT_ID = None
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
LEADS_FILE = "/tmp/leads.json"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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

FOLLOWUPS = [
    {"stage": 1, "delay_hours": 24,
     "text": "Hi again! 👋 Still thinking about the course?\n\nHere's what our students say:\n\"I was sceptical at first, but after 30 days I was consistently profitable. Best investment I ever made.\" — Ahmad R.\n\n📅 Next KL intake is filling fast. Only 50 seats.\n\n👉 Register: https://whatsform.com/ghwpgv",
     "button": {"text": "📝 Register Now", "url": "https://whatsform.com/ghwpgv"}},
    {"stage": 2, "delay_hours": 72,
     "text": "Hey! Just a heads up — **only 12 seats left** for the upcoming KL intake. 🚀\n\n1,200+ students already transformed their trading. Don't miss your chance.\n\n👉 Secure your seat now: https://whatsform.com/ghwpgv\n\nOr ask me anything!",
     "button": {"text": "💬 Ask Hafizzat", "url": "https://wa.me/60133355669"}},
    {"stage": 3, "delay_hours": 168,
     "text": "⚠️ *Last Call!*\n\nSeats for Turn Charts Into Cashflow are almost gone.\n\nAfter this, next intake date is TBD.\n\n👉 https://whatsform.com/ghwpgv",
     "button": {"text": "🚀 Register Now", "url": "https://whatsform.com/ghwpgv"}}
]

def process_followups():
    leads = load_leads(); now = int(time.time()); sent = 0
    for uid, lead in leads.items():
        if lead.get("opted_out"): continue
        cs = lead.get("followup_stage", 0)
        if cs >= len(FOLLOWUPS): continue
        fu = FOLLOWUPS[cs]
        if (now - lead.get("first_seen", now)) >= fu["delay_hours"] * 3600:
            buttons = {"inline_keyboard": [[fu["button"], {"text": "⏹ Stop", "callback_data": f"optout_{uid}"}]]}
            try:
                send_msg(lead["chat_id"], fu["text"], reply_markup=buttons)
                leads[uid]["followup_stage"] = cs + 1; leads[uid]["followup_sent_at"].append(int(time.time())); sent += 1
            except: pass
    save_leads(leads); return sent

def main_menu():
    return {"inline_keyboard": [
        [{"text": "🤖 HR AI - Trading Systems", "callback_data": "hr_ai"}],
        [{"text": "📚 Turn Charts Into Cashflow", "callback_data": "course"}],
        [{"text": "💰 Pricing", "callback_data": "pricing"}],
        [{"text": "💳 How to Pay", "callback_data": "payment"}],
        [{"text": "📞 Contact / WhatsApp", "callback_data": "contact"}],
        [{"text": "🎥 YouTube", "url": "https://youtube.com/@HafizzatRusli"}]
    ]}
def back_button():
    return {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "main_menu"}]]}
def pricing_buttons():
    return {"inline_keyboard": [
        [{"text": "💳 How to Pay", "callback_data": "payment"}],
        [{"text": "💬 Ask HR AI", "callback_data": "contact"}],
        [{"text": "📚 Ask Course", "callback_data": "course_contact"}],
        [{"text": "⬅️ Back", "callback_data": "main_menu"}]
    ]}
def payment_buttons():
    return {"inline_keyboard": [
        [{"text": "💬 WhatsApp to Pay", "url": "https://wa.me/60133355669"}],
        [{"text": "⬅️ Back", "callback_data": "main_menu"}]
    ]}

WELCOME = "👋 *Assalamualaikum & Welcome!*\n\nI'm Lia, Hafizzat Rusli's assistant. How can I help?"
HR_AI_MSG = "🤖 *HR AI — Trading Systems*\n\n✅ Delta-neutral strategies\n✅ Quant-tested\n✅ FxPro compatible\n✅ 24/7 execution\n\n👉 Self-Serve: RM28,149\n👉 Turnkey: RM45,873\n\nTap Contact for case studies."
COURSE_MSG = "📚 *Turn Charts Into Cashflow*\n\n✅ 1,200+ Students\n✅ 87% Profitable in 30 Days\n✅ Lifetime Access + VIP Group\n\n⚠️ Only 50 Seats — Next: KL\n\n💎 Basic: RM5,000\n💎 Intermediate: RM10,000\n💎 Advanced: RM20,000\n💎 Ultimate: RM40,000\n💎 Infinite: RM80,000"
PRICING_MSG = "💰 *Pricing*\n━━━━━━━━━━━\n🤖 HR AI\n• Self-Serve: RM28,149\n• Turnkey: RM45,873\n\n📚 Course\n• Basic: RM5k • Inter: RM10k\n• Adv: RM20k • Ultra: RM40k\n• Infinite: RM80k\n\n💳 BTC / USDT / USDC / Bank Transfer"
PAYMENT_MSG = "💳 *Payment Methods*\n━━━━━━━━━━━\n\n🏦 Bank Transfer (Course):\nRequest invoice via WhatsApp\n\n₿ *Bitcoin (BTC):*\n`bc1q5qt4qrf536q7zmrfxzcvaulpwlfa66hyuhqku9`\n\n₿ *USDT / USDC (ERC20):*\n`0xeaaa4efaaf0f9dde2c0928e1a1c2667d8af99b89`\n\n📱 After payment, send screenshot to WhatsApp for access!"
CONTACT_MSG = "📞 *Contact*\n💬 WhatsApp: wa.me/60133355669\n📱 Telegram: @MsRinaC\n📧 IG/FB: @hafizzatrusli\n🎥 YouTube: @HafizzatRusli"
COURSE_CONTACT_MSG = "📚 *Register*\n\n📱 https://whatsform.com/ghwpgv\n💬 We'll WhatsApp to reserve your seat!\n\nOr WA: wa.me/60133355669"

def send_msg(cid, text, rm=None, pm="Markdown"):
    p = {"chat_id": cid, "text": text, "parse_mode": pm}
    if rm: p["reply_markup"] = json.dumps(rm)
    try: return requests.post(f"{BASE_URL}/sendMessage", json=p, timeout=10).json()
    except: return None
def answer_cbq(cid, t):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": cid, "text": t, "show_alert": False}, timeout=5)
def edit_msg(cid, mid, text, rm=None, pm="Markdown"):
    p = {"chat_id": cid, "message_id": mid, "text": text, "parse_mode": pm}
    if rm: p["reply_markup"] = json.dumps(rm)
    requests.post(f"{BASE_URL}/editMessageText", json=p, timeout=10)
def notify_admin(t):
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID: send_msg(ADMIN_CHAT_ID, f"📬 *New Lead*\n\n{t}")

def handle_start(chat_id):
    send_msg(chat_id, WELCOME, main_menu())
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID is None:
        ADMIN_CHAT_ID = chat_id
        send_msg(chat_id, "✅ You're now admin. You'll get lead alerts.")
    track_lead(chat_id, "started")

def handle_callback(chat_id, message_id, data, cb_id):
    if data.startswith("optout_"):
        uid = data.split("_",1)[1]
        leads = load_leads()
        if uid in leads: leads[uid]["opted_out"] = True; save_leads(leads)
        answer_cbq(cb_id, "Unsubscribed ✅")
        edit_msg(chat_id, message_id, "Unsubscribed ✅\n\nMenu still open!", main_menu())
        return
    actions = {"main_menu": (WELCOME, main_menu()), "hr_ai": (HR_AI_MSG, back_button()),
               "course": (COURSE_MSG, back_button()), "pricing": (PRICING_MSG, pricing_buttons()),
               "payment": (PAYMENT_MSG, payment_buttons())}
    if data in actions:
        t, kb = actions[data]; edit_msg(chat_id, message_id, t, kb); answer_cbq(cb_id, "👌")
        track_lead(chat_id, data)
        if data in ("hr_ai","course"): notify_admin(f"👤 Viewed *{data.replace('_',' ').title()}*")
    elif data == "contact":
        edit_msg(chat_id, message_id, CONTACT_MSG, {"inline_keyboard": [[{"text":"💬 WhatsApp","url":"https://wa.me/60133355669"}],[{"text":"⬅️ Back","callback_data":"main_menu"}]]})
        answer_cbq(cb_id, "Contact"); track_lead(chat_id,"contact"); notify_admin("👤 Requested *Contact* — potential lead!")
    elif data == "course_contact":
        edit_msg(chat_id, message_id, COURSE_CONTACT_MSG, {"inline_keyboard": [[{"text":"📱 Register","url":"https://whatsform.com/ghwpgv"}],[{"text":"💬 WhatsApp","url":"https://wa.me/60133355669"}],[{"text":"⬅️ Back","callback_data":"main_menu"}]]})
        answer_cbq(cb_id,"Course"); track_lead(chat_id,"course_contact"); notify_admin("👤 Wants to *join course*!")

def handle_message(chat_id, text):
    global ADMIN_CHAT_ID
    track_lead(chat_id, f"msg:{text[:50]}")
    if ADMIN_CHAT_ID and chat_id != ADMIN_CHAT_ID:
        notify_admin(f"📩 *Msg*\nChat: `{chat_id}`\nText: _{text}_")
        send_msg(chat_id, "Thanks! Hafizzat will reply soon 🙏\n\nCheck menu 👆", main_menu())

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status":"ok","bot":"@Lia_489_bot"})

@app.route("/webhook", methods=["POST"])
def webhook():
    u = request.get_json()
    try:
        if "callback_query" in u:
            cb = u["callback_query"]
            handle_callback(cb["message"]["chat"]["id"], cb["message"]["message_id"], cb.get("data",""), cb.get("id"))
        elif "message" in u:
            m = u["message"]; cid = m["chat"]["id"]; t = m.get("text","")
            if t == "/start": handle_start(cid)
            else: handle_message(cid, t)
    except Exception as e: logging.error(f"E: {e}")
    return jsonify({"ok": True})

@app.route("/cron", methods=["GET"])
def cron():
    s = process_followups(); l = load_leads()
    return jsonify({"status":"ok","sent":s,"total":len(l),"active":sum(1 for x in l.values() if not x.get("opted_out"))})

@app.route("/leads", methods=["GET"])
def report():
    l = load_leads(); total=len(l); active=sum(1 for x in l.values() if not x.get("opted_out"))
    s={1:0,2:0,3:0}
    for x in l.values():
        st=x.get("followup_stage",0)
        if st in s: s[st]+=1
    return jsonify({"total":total,"active":active,"opted_out":total-active,"stage1":s[1],"stage2":s[2],"stage3":s[3]})

def set_webhook():
    u = os.environ.get("PUBLIC_URL","")
    if u:
        r = requests.get(f"{BASE_URL}/setWebhook?url={u}/webhook")
        logging.info(f"WH: {r.json()}")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
