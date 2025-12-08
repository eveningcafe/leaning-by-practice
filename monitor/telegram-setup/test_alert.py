#!/usr/bin/env python3
"""
Test Telegram Alert

Sends a sample alert message to verify Telegram notification is working.
This mimics the format Alertmanager will use.

Usage:
    python test_alert.py <BOT_TOKEN> <CHAT_ID>

Or with environment variables:
    export TELEGRAM_BOT_TOKEN=your_token
    export TELEGRAM_CHAT_ID=your_chat_id
    python test_alert.py
"""

import os
import sys
import requests
from datetime import datetime


def send_alert(token: str, chat_id: str, alert_type: str = "firing"):
    """Send a sample alert message."""

    if alert_type == "firing":
        message = """🔴 <b>FIRING: BackendDown</b>

<b>Alert:</b> BackendDown
<b>Severity:</b> critical
<b>Instance:</b> backend1:5000
<b>Job:</b> backends

<b>Summary:</b> Backend backend1:5000 is down

<b>Started:</b> {time}

<a href="http://localhost:9090/alerts">View in Prometheus</a> | <a href="http://localhost:9093">View in Alertmanager</a>
""".format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:
        message = """🟢 <b>RESOLVED: BackendDown</b>

<b>Alert:</b> BackendDown
<b>Instance:</b> backend1:5000

<b>Resolved at:</b> {time}

The backend is now operational.
""".format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload)
    return response.status_code == 200, response.json()


def main():
    # Get credentials from args or environment
    if len(sys.argv) >= 3:
        token = sys.argv[1]
        chat_id = sys.argv[2]
    else:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Usage: python test_alert.py <BOT_TOKEN> <CHAT_ID>")
        print("\nOr set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN=your_token")
        print("  export TELEGRAM_CHAT_ID=your_chat_id")
        sys.exit(1)

    print("Sending test FIRING alert...")
    success, response = send_alert(token, chat_id, "firing")

    if success:
        print("Firing alert sent!")
    else:
        print(f"Failed: {response}")
        sys.exit(1)

    print("\nSending test RESOLVED alert...")
    success, response = send_alert(token, chat_id, "resolved")

    if success:
        print("Resolved alert sent!")
        print("\nCheck your Telegram for the test messages.")
    else:
        print(f"Failed: {response}")
        sys.exit(1)


if __name__ == "__main__":
    main()
