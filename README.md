# Dark GPT 🤖

Dark GPT is an advanced Telegram bot that allows users to interact with AI models through a flexible and extensible architecture.  
The project is built in Python and leverages multiple AI APIs to deliver dynamic, unrestricted, and customizable AI-powered conversations.

> ⚠️ This project is intended for **educational and experimental purposes**.  
> The developer is not responsible for how end users interact with or utilize connected AI APIs.

---

## ✨ Features

- 🤖 AI-powered Telegram bot
- 🔌 Supports **multiple AI APIs**
- ⚙️ Modular and extensible architecture
- 💬 Real-time chat interaction
- 🧠 Custom prompt handling
- 🚀 Easy to deploy and customize
- 🐍 Built with Python

---

## 🛠 Tech Stack

- **Language:** Python  
- **Telegram Library:** `python-telegram-bot`  
- **APIs:** Multiple AI service providers  
- **Platform:** Telegram  

---

🚀 Getting Started
1️⃣ Clone the Repository
git clone https://github.com/m-hasani-dev/darkGPT.git
cd darkGPT

2️⃣ Create Virtual Environment (Recommended)
```
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```
3️⃣ Install Dependencies
```
pip install -r requirements.txt
```
🔑 Configuration

Create a Telegram bot via @BotFather

Obtain your bot token

Configure API keys for the AI providers you want to use

Add them to your configuration file or environment variables

Example:
```
in .env file:
BOT_TOKEN=your telegram bot token
BOT_USERNAME="username of your bot like: @darkgpt_bot"
OWNER_ID=put admin id's here
LIARA_API_KEY=api key from ai
SYSTEM_PROMPT=put system prompt here. you can find mine in sysprompt.txt file
```
