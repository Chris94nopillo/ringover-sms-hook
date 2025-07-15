from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET    = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    try:
        data = request.get_json()
        print("✅ Reçu :", data)

        # Extraire les champs
        phone         = data.get("phone", "")
        firstname     = data.get("firstname", "")
        meeting_time  = data.get("meeting_time", "")
        password      = data.get("password") or data.get("secret")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Authentification du webhook
        if password != WEBHOOK_SECRET:
            print("❌ Secret invalide")
            return jsonify({"error": "Unauthorized"}), 401

        # Champs requis
        if not phone or not firstname or not meeting_time:
            print("❌ Champs manquants")
            return jsonify({"error": "Missing required fields"}), 400

        # Nettoyage du numéro : on ne garde que les chiffres
        clean_phone = "".join(ch for ch in phone if ch.isdigit())

        # Construction du message
        message = f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}. À très vite !"

        # Préparation de la requête Ringover
        payload = {
            "number": clean_phone,
            "text":   message,
            "from":   from_alphanum
        }
        headers = {
            "Authorization": RINGOVER_API_KEY,
            "Content-Type":  "application/json"
        }

        # Envoi
        resp = requests.post(
            "https://public-api.ringover.com/v2/sms",
            json=payload,
            headers=headers
        )

        print("📤 Vers Ringover:", payload)
        print("📥 Ringover a répondu:", resp.status_code, resp.text)

        if resp.status_code == 200:
            return jsonify({"success": True, "details": resp.json()}), 200
        else:
            return jsonify({"error": "Ringover API error", "details": resp.text}), resp.status_code

    except Exception as e:
        print("🔥 Erreur inattendue :", e)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
