import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load Stripe keys from environment
stripe.api_key = os.environ['STRIPE_SECRET_KEY']
endpoint_secret = os.environ['STRIPE_WEBHOOK_SECRET']

@app.route('/')
def index():
    return 'AutoEcho is alive 💚'

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print('⚠️ Invalid payload:', e)
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print('⚠️ Invalid signature:', e)
        return 'Invalid signature', 400

    # ✅ Event type handling
    print(f"🔔 Event received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"✅ Checkout complete: {session['id']}")

    elif event['type'] == 'invoice.paid':
        print("💸 Invoice paid.")

    elif event['type'] == 'invoice.payment_failed':
        print("❌ Payment failed.")

    elif event['type'] == 'customer.subscription.created':
        print("✨ Subscription created.")

    elif event['type'] == 'customer.subscription.updated':
        print("🛠 Subscription updated.")

    elif event['type'] == 'customer.subscription.deleted':
        print("🗑 Subscription deleted.")

    # Acknowledge receipt
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(port=8080)
