#!/usr/bin/env python3
"""
Telegram Bot Setup Helper

This script helps you:
1. Verify your bot token is valid
2. Get your chat ID automatically
3. Send a test message to verify everything works

Prerequisites:
1. Create a bot via @BotFather on Telegram:
   - Open Telegram, search for @BotFather
   - Send /newbot
   - Follow prompts to name your bot
   - Copy the token provided

2. Start a chat with your bot:
   - Search for your bot by username
   - Click "Start" or send /start

Usage:
    python setup_bot.py <BOT_TOKEN>

Example:
    python setup_bot.py 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
"""

import sys
import requests


def get_bot_info(token: str) -> dict | None:
    """Verify bot token and get bot info."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return None


def get_updates(token: str) -> list:
    """Get recent messages sent to the bot."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("result", [])
    return []


def send_test_message(token: str, chat_id: int) -> bool:
    """Send a test message to verify setup."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ Alertmanager Telegram integration is working!\n\nYou will receive alerts here.",
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_bot.py <BOT_TOKEN>")
        print("\nTo get a bot token:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow the prompts")
        print("3. Copy the token provided")
        sys.exit(1)

    token = sys.argv[1]

    # Step 1: Verify bot token
    print("=" * 50)
    print("Step 1: Verifying bot token...")
    print("=" * 50)

    bot_info = get_bot_info(token)
    if not bot_info:
        print("ERROR: Invalid bot token!")
        print("Make sure you copied the full token from @BotFather")
        sys.exit(1)

    bot_name = bot_info["result"]["username"]
    print(f"Bot verified: @{bot_name}")

    # Step 2: Get chat ID
    print("\n" + "=" * 50)
    print("Step 2: Looking for your chat ID...")
    print("=" * 50)

    updates = get_updates(token)

    if not updates:
        print(f"\nNo messages found. Please:")
        print(f"1. Open Telegram")
        print(f"2. Search for @{bot_name}")
        print(f"3. Click 'Start' or send any message")
        print(f"4. Run this script again")
        sys.exit(1)

    # Extract unique chat IDs
    chat_ids = {}
    for update in updates:
        if "message" in update:
            chat = update["message"]["chat"]
            chat_id = chat["id"]
            chat_type = chat["type"]

            if chat_type == "private":
                name = chat.get("first_name", "") + " " + chat.get("last_name", "")
            else:
                name = chat.get("title", "Group")

            chat_ids[chat_id] = {"type": chat_type, "name": name.strip()}

    print("\nFound chat(s):")
    for cid, info in chat_ids.items():
        print(f"  Chat ID: {cid}")
        print(f"  Type: {info['type']}")
        print(f"  Name: {info['name']}")
        print()

    # Use the first chat ID for testing
    chat_id = list(chat_ids.keys())[0]

    # Step 3: Send test message
    print("=" * 50)
    print("Step 3: Sending test message...")
    print("=" * 50)

    if send_test_message(token, chat_id):
        print("Test message sent successfully!")
    else:
        print("ERROR: Failed to send test message")
        sys.exit(1)

    # Final output
    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)
    print("\nAdd these to your .env file:")
    print(f"  TELEGRAM_BOT_TOKEN={token}")
    print(f"  TELEGRAM_CHAT_ID={chat_id}")
    print("\nOr update alertmanager.yml directly with these values.")


if __name__ == "__main__":
    main()
