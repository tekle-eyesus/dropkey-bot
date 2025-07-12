#  DropKey Bot

A **privacy-focused Telegram bot** that enables secure and anonymous file sharing without requiring usernames or phone numbers. Users share a unique, temporary **Drop ID** to receive files or messages safely.

---

##  Features

-  **Anonymous File & Message Sharing**
  - Senders only need the receiver’s **Drop ID** to send files/messages.
  - No usernames or phone numbers required.

-  **Drop ID Management**
  - Users can generate **single-use** or **expiring Drop IDs**.
  - Disable/reactivate Drop IDs anytime.

-  **Inbox PIN Protection**
  - Protect your inbox with a PIN to prevent unauthorized access.

-  **Secure Storage**
  - Files and messages are encrypted at rest and auto-deleted after expiration.

---

##  Architecture Overview


- **Drop IDs**: Random, anonymized addresses (e.g., `a8k4z9`) assigned by the bot.
- **Bot**: Acts as the central agent for file/message delivery.
- **Database**: Stores Drop ID mappings, inbox PINs (hashed), and expiration times.
- **File Storage**: Temporary file holding (using Telegram or external storage like AWS S3).

---

##  Tech Stack

- **Bot Framework**: [Python aiogram](https://docs.aiogram.dev/) / Node.js Telegraf
- **Database**: PostgreSQL (Drop ID + PIN management)
- **File Storage**: Telegram API or AWS S3
- **Security**: PIN hashing (bcrypt), file encryption (AES-256)
- **Hosting**: Heroku / Railway / AWS Lambda

---

##  Core Commands

| Command            | Description                                       |
|---------------------|----------------------------------------------------|
| `/start`           | Start interacting with the bot                    |
| `/create_id`       | Generate a new Drop ID (with optional expiration) |
| `/send [DropID]`   | Send a file or message to a Drop ID               |
| `/inbox`           | Access your inbox (requires PIN)                  |
| `/disable_id`      | Temporarily disable your Drop ID                  |
| `/enable_id`       | Reactivate your Drop ID                            |

---


---

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Motivation
We believe privacy is a fundamental right, and sharing information should not require exposing your personal identity.
