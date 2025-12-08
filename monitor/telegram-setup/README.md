# Telegram Alert Setup

Quick setup guide for Telegram notifications with Alertmanager.

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name (e.g., "My Alert Bot")
4. Choose a username (e.g., "my_alert_bot")
5. Copy the **bot token** provided (looks like `123456789:ABCdefGHI...`)

## Step 2: Get Your Chat ID

1. Search for your new bot in Telegram
2. Click **Start** or send any message to it
3. Run the setup script:

```bash
cd telegram-setup
pip install -r requirements.txt
python setup_bot.py YOUR_BOT_TOKEN
```

This will:
- Verify your token
- Find your chat ID
- Send a test message

## Step 3: Update Configuration

Add your credentials to `../env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Step 4: Test the Alert

```bash
# Test with arguments
python test_alert.py YOUR_BOT_TOKEN YOUR_CHAT_ID

# Or with environment variables
source ../.env
python test_alert.py
```

## Step 5: Start the Monitor Stack

```bash
cd ..
docker-compose up -d
```

## Sending to a Group

To send alerts to a group chat:

1. Add your bot to the group
2. Send a message in the group mentioning the bot
3. Run `setup_bot.py` again to get the group's chat ID
4. Group chat IDs are negative numbers (e.g., `-123456789`)

## Troubleshooting

### "No messages found"
- Make sure you started a chat with the bot
- Send `/start` or any message to the bot
- Run setup_bot.py again

### "Invalid bot token"
- Copy the full token from @BotFather
- Make sure there are no extra spaces

### Alerts not arriving
- Check Alertmanager logs: `docker-compose logs alertmanager`
- Verify credentials in alertmanager.yml
- Test with `test_alert.py` first
