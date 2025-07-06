import os
import stripe
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

# Load secrets from environment
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Route: Home
@app.route('/')
def index():
    return render_template_string("""
    <h2>AutoEcho</h2>
    <p><a href="/buy/basic">Buy Basic Plan</a></p>
    <p><a href="/buy/standard">Buy Standard Plan</a></p>
    <p><a href="/buy/premium">Buy Premium Plan</a></p>
    """)

# Route: Create Checkout Session
@app.route('/buy/<tier>')
def buy(tier):
    prices = {
        "basic": "price_XXXXXXXXXXXX",
        "standard": "price_YYYYYYYYYYYY",
        "premium": "price_ZZZZZZZZZZZZ"
    }
    if tier not in prices:
        return "Invalid plan", 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": prices[tier],
            "quantity": 1,
        }],
        success_url="https://autoecho.xyz/success",
        cancel_url="https://autoecho.xyz/cancel",
    )
    return redirect(session.url, code=303)

# Route: Webhook to handle Stripe events
@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    # Handle events
    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        print("✅ Checkout completed:", data)
    elif event_type == 'invoice.paid':
        print("💸 Invoice paid:", data)
    elif event_type == 'invoice.payment_failed':
        print("❌ Payment failed:", data)
    elif event_type == 'customer.subscription.updated':
        print("🔁 Subscription updated:", data)
    elif event_type == 'customer.subscription.deleted':
        print("🗑️ Subscription canceled:", data)
    elif event_type == 'customer.subscription.created':
        print("📦 Subscription created:", data)
    else:
        print("Unhandled event:", event_type)

    return jsonify({"status": "success"})

# Route: Success + Cancel pages
@app.route('/success')
def success():
    return "<h1>Payment successful!</h1>"

@app.route('/cancel')
def cancel():
    return "<h1>Payment canceled.</h1>"

# Cloud Run-compatible run block
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
