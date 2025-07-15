from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET    = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # —> Toujours caster en str avant strip/replace
    raw_phone     = str(data.get("phone", "")).strip()
    firstname_raw = data.get("firstname", "")
    meeting_time  = data.get("meeting_time", "")
    password      = data.get("password") or data.get("secret")
    from_alphanum = data.get("from_alphanum", "Nopillo")

    if password != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    if not raw_phone or not firstname_raw or not meeting_time:
        return jsonify({"error": "Missing required fields"}), 400

    # Normalisation du numéro
    phone = raw_phone.replace(" ", "").replace("-", "")
    if phone.startswith("+33"):
        phone = "0" + phone[3:]
    if phone.startswith("0"):
        phone = "33" + phone[1:]

    # Capitalisation du prénom
    firstname = firstname_raw.strip().capitalize()

    # Construction du message
    message = f"Bonjour {firstname}, votre RDV avec Npolli est confirmé pour {meeting_time}. Merci et à bientôt !"

    payload = {
        "from_alphanum": from_alphanum,
        "to_number"    : phone,
        "content"      : message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type" : "application/json"
    }

    resp = requests.post(
        "https://public-api.ringover.com/v2/push/sms/v1",
        json=payload,
        headers=headers
    )

    print("📤 Envoi payload :", payload)
    print("📥 Réponse Ringover :", resp.status_code, resp.text)

    if resp.status_code == 200:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Ringover API error", "details": resp.text}), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
