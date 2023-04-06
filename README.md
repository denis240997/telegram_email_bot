# Telegram Email Bot

Telegram Email Bot is a bot that checks your email autonomously for emails containing the same order number. It generates a report from several emails, which is then sent to the user in a Telegram chat. This bot is designed to help you manage your emails more efficiently and stay organized.

## Features

- Automated email scanning: the bot scans your email autonomously to find emails with the same order number.
- Digest creation: the bot creates a report from several emails with the same order number.
- Telegram integration: the bot sends the report to the user in a Telegram chat.
- Customizable settings: you can configure the bot to scan for specific keywords or search for emails from specific senders.

## Installation

To install the Telegram Email Bot, follow these steps:

1. Clone the repository:

```
git clone https://github.com/your-username/telegram_email_bot.git
```

2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Set up your email and Telegram credentials:

In the project's root directory, create a new file called `settings.txt` with following content:

```
\#Bot credentials
API_ID=YOUR_TELEGRAM_API_ID
API_HASH=YOUR_TELEGRAM_API_HASH
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
```

5. Export environment variables:

```
source <(grep -v '^#' settings.txt | xargs -I {} echo "export {}")
```

4. Run the bot:

```
python main.py
```

5. Or run app in development mode:

```
chmode +x dev_script.py
source ./dev_script.py
```

## Usage

Once the bot is up and running, it will automatically scan your email for emails with the same order number. When it finds several emails with the same order number, it will generate a report and send it to you in a Telegram chat.

## Contributing

If you want to contribute to the Telegram Email Bot, you can:

- Report bugs and issues by creating a new issue in the repository.
- Suggest new features and improvements by creating a new issue in the repository.
- Fork the repository, make changes, and submit a pull request.
