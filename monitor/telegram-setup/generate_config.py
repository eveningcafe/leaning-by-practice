#!/usr/bin/env python3
"""
Generate alertmanager.yml with Telegram credentials

This script reads your .env file and generates the alertmanager.yml
with the correct bot_token and chat_id values.

Usage:
    python generate_config.py

This will:
1. Read TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from ../.env
2. Update ../alertmanager.yml with these values
"""

import os
import re
import sys
from pathlib import Path


def load_env(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def update_alertmanager_config(config_path: Path, bot_token: str, chat_id: str):
    """Update alertmanager.yml with Telegram credentials."""
    with open(config_path) as f:
        content = f.read()

    # Replace bot_token
    content = re.sub(
        r"bot_token:\s*'[^']*'",
        f"bot_token: '{bot_token}'",
        content
    )

    # Replace chat_id (it's an integer, no quotes)
    content = re.sub(
        r"chat_id:\s*\d+.*",
        f"chat_id: {chat_id}",
        content
    )

    with open(config_path, 'w') as f:
        f.write(content)

    print(f"Updated {config_path}")


def main():
    script_dir = Path(__file__).parent
    env_path = script_dir.parent / '.env'
    config_path = script_dir.parent / 'alertmanager.yml'

    # Load .env
    env_vars = load_env(env_path)

    bot_token = env_vars.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = env_vars.get('TELEGRAM_CHAT_ID', '')

    # Validate
    if not bot_token or bot_token == 'your_bot_token_here':
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        print(f"Please update {env_path}")
        sys.exit(1)

    if not chat_id or chat_id == 'your_chat_id_here':
        print("ERROR: TELEGRAM_CHAT_ID not set in .env")
        print(f"Please update {env_path}")
        sys.exit(1)

    # Validate chat_id is numeric
    try:
        int(chat_id)
    except ValueError:
        print(f"ERROR: TELEGRAM_CHAT_ID must be a number, got: {chat_id}")
        sys.exit(1)

    # Update config
    update_alertmanager_config(config_path, bot_token, chat_id)

    print("\nConfiguration updated successfully!")
    print("\nNext steps:")
    print("1. Restart alertmanager: docker-compose restart alertmanager")
    print("2. Test by killing a backend: docker-compose stop backend1")
    print("3. Check your Telegram for the alert!")


if __name__ == "__main__":
    main()
