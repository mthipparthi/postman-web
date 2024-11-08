import hmac
import json
from base64 import b64encode
from datetime import datetime
from hashlib import sha512
from time import mktime
from urllib.parse import quote
from wsgiref.handlers import format_date_time

import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for flash messages


XCOVER_API_KEY = "TESTAPIKEY"
XCOVER_SECRET = "testsecret"


import hmac
from base64 import b64encode
from datetime import datetime
from hashlib import sha512
from time import mktime
from urllib.parse import quote
from wsgiref.handlers import format_date_time


def generate_signed_headers(key, secret):
    """
    Generate signed headers for authentication.

    Args:
        key (str): API key.
        secret (str): Secret key for signing.

    Returns:
        dict: Headers including Date, Authorization, and X-Api-Key.
    """
    # Generate the current HTTP date
    now = datetime.utcnow()
    date = format_date_time(mktime(now.timetuple()))

    # Create the signature
    raw = f"date: {date}"
    hashed = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), sha512).digest()
    signature = quote(b64encode(hashed), safe="")

    # Build the Authorization header
    auth = (
        f'Signature keyId="{key}",algorithm="hmac-sha512",' f'signature="{signature}"'
    )

    # Return the headers
    return {
        "Date": date,
        "Authorization": auth,
        "X-Api-Key": key,
        "Content-Type": "application/json",
    }


# Function to call downstream system
def call_downstream_system(host, data):
    # headers = {
    #     "X-Api-Key": API_KEY,
    #     "Authorization": f'Signature keyId="{API_KEY}",algorithm="hmac-sha1",signature="{generate_signature()}"',
    #     "Content-Type": "application/json",
    #     "Date": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
    # }

    headers2 = generate_signed_headers(XCOVER_API_KEY, XCOVER_SECRET)

    DOWNSTREAM_URL = f"{host}/api/v2/partners/AAAAA/quotes/?fast_quote=false"

    response = requests.post(
        DOWNSTREAM_URL, headers=headers2, data=json.dumps(data), verify=False
    )
    return response.json(), response.status_code


# Route for the HTML form
@app.route("/")
def index():
    return render_template("quote_form.html")


# Route to handle form submission
@app.route("/submit", methods=["POST"])
def submit_form():
    try:
        host = request.form.get("partner_host")
        # Get form data
        currency = request.form.get("currency") or "EUR"
        customer_country = request.form.get("customer_country")
        partner_transaction_id = request.form.get("partner_transaction_id")
        customer_language = request.form.get("customer_language")
        customer_postcode = request.form.get("customer_postcode")
        policy_start_date = request.form.get("policy_start_date")
        policy_end_date = request.form.get("policy_end_date")

        # Construct payload
        payload = {
            "currency": currency,
            "customer_country": customer_country,
            "partner_transaction_id": partner_transaction_id,
            "customer_language": customer_language,
            "customer_postcode": customer_postcode,
            "request": [
                {
                    "policy_type": "travel_flight_cancellation_cover",
                    "policy_type_version": "1",
                    "policy_start_date": policy_start_date,
                    "policy_end_date": policy_end_date,
                    "insured": [{}, {}],
                }
            ],
        }

        # Call downstream system
        response_data, status_code = call_downstream_system(host, payload)

        return render_template("quote_response.html", formatted_json=response_data)

    except Exception as e:
        breakpoint()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("index"))
