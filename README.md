<div align="center">

  <!-- LOGO PLACEHOLDER - REPLACE THE LINK BELOW -->
  <img src="https://res.cloudinary.com/dewvz4zxk/image/upload/v1765444124/logooo_ayvujz.jpg" alt="DropKey Bot Logo" width="70" height="auto" />

  # DropKey Bot
  
  **Secure. Anonymous. Transient.**
  <br>
  The privacy-focused Telegram bot for sharing files without a trace.

  <!-- BADGES -->
  <p>
    <a href="https://github.com/username/dropkey-bot/graphs/contributors">
      <img src="https://img.shields.io/badge/contributors-welcome-orange.svg" alt="Contributors" />
    </a>
    <a href="https://github.com/username/dropkey-bot/issues">
      <img src="https://img.shields.io/badge/issues-welcome-teal.svg" alt="Issues" />
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    </a>
    <a href="https://docs.aiogram.dev/">
      <img src="https://img.shields.io/badge/built%20with-Aiogram-red" alt="Aiogram" />
    </a>
  </p>

  <h4>
    <a href="#features">Features</a>
    <span> · </span>
    <a href="#installation">Installation</a>
    <span> · </span>
    <a href="#architecture">Architecture</a>
    <span> · </span>
    <a href="#contributing">Contributing</a>
  </h4>
</div>

---

## 🚀 Overview

**DropKey Bot** redefines privacy on Telegram. We believe sharing information shouldn't require exposing your personal identity (username or phone number). 

By utilizing unique, temporary **Drop IDs**, users can receive files and messages securely. Once the transaction is done, the ID vanishes—along with any digital footprint.

---

## ✨ Features

### 🔒 Anonymity First
- **No Personal Data**: Senders only need a **Drop ID**. No usernames, no phone numbers, no profile links.
- **Masked Delivery**: The bot acts as a middleman, ensuring the sender and receiver never interact directly.

### 🛡️ Drop ID Management
- **Ephemeral IDs**: Generate **single-use** IDs that self-destruct after one transfer.
- **Time-Bound**: Create IDs that expire automatically after a set time.
- **Kill Switch**: Manually disable or reactivate your Drop ID instantly.

### 🔐 Security & Storage
- **Inbox PIN**: A second layer of defense. Access your received files only after entering your private PIN.
- **Zero-Knowledge Storage**: Files and messages are encrypted at rest and auto-deleted immediately after expiration.

---

## 🛠 Architecture

DropKey acts as a privacy proxy between two users.

```mermaid
flowchart LR
    Sender((Sender)) -->|1. Sends File to Bot| Bot[🤖 DropKey Bot]
    Bot -->|2. Validates DropID| DB[(Database)]
    DB -->|3. Returns Encrypted Route| Bot
    Bot -->|4. Forwards File| Receiver((Receiver))
    
    style Bot fill:#f9f,stroke:#333,stroke-width:2px
    style DB fill:#bbf,stroke:#333,stroke-width:2px
```
- **Drop IDs:** Random, anonymized alphanumeric strings (e.g., `a8k4z9`).
- **The Bot:** Central agent for delivery; scrubs metadata before forwarding.
- **Database:** Stores ID mappings and hashed PINs (BCrypt).
- **Storage:** Temporary holding via Telegram API or encrypted AWS S3 buckets.

## 💻 Tech Stack

| Component  | Technology                                    |
|------------|-----------------------------------------------|
| Framework  | Python Aiogram / Node.js Telegraf             |
| Database   | PostgreSQL (Relational Data)                  |
| Caching    | Redis (Rate limiting & Temporary IDs)         |
| Security   | BCrypt (PIN Hashing), AES-256 (File Encryption) |
| Hosting    | Heroku / Railway / AWS Lambda                 |

## 🕹 Core Commands

| Command        | Description                                                   |
|----------------|---------------------------------------------------------------|
| `/start`       | Initialize the bot and view the main menu.                    |
| `/create_id`   | Generate a new Drop ID (prompts for Single-use or Time-limit).|
| `/send [DropID]` | Upload a file or text to a specific Drop ID.               |
| `/inbox`       | View received content (requires PIN entry).                   |
| `/disable_id`  | Temporarily pause your current ID (sender receives error).   |
| `/enable_id`   | Reactivate your paused Drop ID.                               |
| `/nuke`        | **Danger Zone:** Delete all your IDs and data permanently.    |

## ⚡ Installation & Setup

To run **DropKey** locally for development:

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dropkey-bot.git
cd dropkey-bot
```
### 2. Install Dependencies

```bash
pip install -r requirements.txt

# OR for Node
npm install
```
### 3. Environment Variables  
Create a `.env` file in the root directory:

```env
BOT_TOKEN=your_telegram_bot_token
DB_URI=postgresql://user:pass@localhost:5432/dropkey
AWS_ACCESS_KEY=your_aws_key
```
### 4. Run the Bot

```bash
python main.py
```
## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m "Add some AmazingFeature"`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

## 📜 Motivation

"Privacy is not an option, and it shouldn't be the price we accept for just getting on the internet."

We built **DropKey** because we believe sharing a file shouldn't mean sharing your identity. Whether for whistleblowers, journalists, or just privacy-conscious individuals, DropKey ensures your data moves, but your identity stays put.

<div align="center">
<sub>Built with ❤️ by Tekleeyesus M.</sub>
</div>
