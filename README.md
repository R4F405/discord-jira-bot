# Discord-Jira Bot 🤖

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-library-7289DA.svg)](https://github.com/Rapptz/discord.py)

An integration bot for Discord and Jira that allows querying ticket 🎫 information from Discord and sending Jira event notifications to Discord channels.

## ✨ Features

- **💻 Discord Commands**:
  - `!jira info`: Displays information about available commands.
  - `!jira <ticket_id>`: Retrieves detailed information for a specific ticket.
  - `!jira assigned <user>`: Lists tickets assigned to a specific user.
  - `!jira finished <user>`: Lists tickets completed or in QA by a specific user.
  - `!jira dev <user>`: Lists tickets in progress for a specific user.

- **🔔 Jira to Discord Notifications**:
  - New ticket creation
  - Ticket updates (status changes, summary, priority)
  - Comments on tickets
  - Assignment changes
  - Description updates
  - File attachments
  - Ticket deletion

## ✅ Requirements

- Python 3.8+
- A Discord account
- A Jira account
- A Discord server where you have permissions to add bots

## 🔗 Dependencies

- discord.py
- requests
- flask
- python-dotenv

## 🚀 Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/R4F405/discord-jira-bot.git
    cd discord-jira-bot
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/MacOS
    source .venv/bin/activate

    pip install -r requirements.txt
    ```

3.  Configure environment variables (see "⚙️ Configuration" section).

4.  Run the bot:
    ```bash
    python BotJira.py
    ```

## ⚙️ Configuration

### 1. 📄 Create a .env file

Create a `.env` file in the project root with the following content:

```
DISCORD_TOKEN=your_discord_token
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_email@example.com
JIRA_API_TOKEN=your_jira_api_token
DISCORD_CHANNEL_ID=discord_channel_id
```

### 2. 🔑 Obtain Discord Token

To get the Discord token:

1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click on "New Application" and give it a name.
3.  Navigate to the "Bot" section in the side panel.
4.  Click "Add Bot".
5.  Under the bot's name, click "Reset Token" and copy the generated token.
6.  Ensure you enable "Privileged Gateway Intents":
    -   MESSAGE CONTENT INTENT
    -   PRESENCE INTENT
    -   SERVER MEMBERS INTENT

### 3. 📨 Invite the Bot to Your Server

1.  In the [Discord Developer Portal](https://discord.com/developers/applications), select your application.
2.  Go to "OAuth2" → "URL Generator".
3.  Select the following permissions:
    -   Under "SCOPES": `bot`
    -   Under "BOT PERMISSIONS": Send Messages, Read Message History, etc. (or simply "Administrator" for testing).
4.  Copy the generated URL, paste it into your browser, and select the server where you want to add the bot.

### 4. 🔑 Configure Jira Tokens

To get the Jira API token:

1.  Log in to [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens).
2.  Go to "Security" → "API token".
3.  Click "Create API token".
4.  Give it a descriptive name (e.g., "Discord Bot") and click "Create".
5.  Copy the generated token.

### 5. 🆔 Obtain Discord Channel ID

1.  In Discord, go to "User Settings" → "Advanced".
2.  Enable "Developer Mode".
3.  Right-click on the channel where you want to receive notifications and select "Copy ID".

### 6. 🎣 Configure Jira Webhooks

For Jira to send notifications to your bot:

1.  In Jira, go to "Settings" (cog icon) → "System" → "Webhooks" (under "Advanced").
2.  Click "Create a Webhook".
3.  Configure the following:
    -   **Name**: Discord Bot
    -   **URL**: `http://your-server:8080/webhook` (you will need to expose your server to the internet or use ngrok for testing).
    -   **Events**: Select the events you want to trigger notifications (Issue created, Comment created, etc.).

### 7. 🧪 Configure ngrok for Local Testing

For local testing, you can use ngrok to expose your Flask server to the internet, allowing Jira to send webhooks to your application:

1.  Download and install [ngrok](https://ngrok.com/download).
2.  Create a free ngrok account and follow the instructions to get your authentication token.
3.  Authenticate your ngrok installation (you only need to do this once):
    ```bash
    ngrok config add-authtoken YOUR_NGROK_TOKEN
    ```
4.  Start your bot so the Flask server is running on port 8080.
5.  In another terminal, run ngrok to expose port 8080:
    ```bash
    ngrok http 8080
    ```
6.  Ngrok will provide you with a public URL (e.g., `https://abc123.ngrok.io`).
7.  Use this URL in your Jira webhook configuration:
    `https://abc123.ngrok.io/webhook`

**Note**: Each time you start ngrok, you will get a different URL, so you will need to update the URL in the Jira webhook configuration if you restart ngrok.

For a production environment, you will need a server with a public IP or a cloud service like Heroku, AWS, etc.

## 🏗️ Architecture

The bot operates with two main components:

1.  **Discord Bot**: Listens for commands in Discord and responds with information from Jira.
2.  **Flask Server**: Receives webhooks from Jira and sends notifications to Discord.

Both components run concurrently using Python threads.

## 🎨 Customization

You can customize:

-   Response messages in Discord.
-   Notification format.
-   Event types that trigger notifications.

## 🛠️ Troubleshooting

-   **Bot is not responding**: Verify that the Discord token is correct and that the bot has the necessary permissions.
-   **Not receiving Jira notifications**: Verify that the webhook URL is accessible from the internet.
-   **Jira authentication error**: Verify that the email and API token are correct.

## 🔒 Security

The `.env` file contains sensitive information and should not be shared or uploaded to public repositories. It is included in `.gitignore` by default.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome. Please submit a pull request or open an issue to discuss proposed changes.
