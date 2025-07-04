# 🤖 Union Auto-Swap Bot

A purpose-built script designed to automate daily swap transactions on the Union testnet, helping you maintain consistent on-chain activity with minimal effort.

<div align="center">
  
[![Telegram](https://img.shields.io/badge/Community-Airdrop_ALC-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/airdropalc/402)

</div>

---

## ✨ Key Features

* **🔁 Automated Daily Swaps:** Set it up once, and the bot will automatically perform swaps for you every day.
* **🌐 Optional Proxy Support:** Easily route traffic through proxies for enhanced privacy and to avoid IP-based limitations.
* **🔥 Fire-and-Forget:** Designed for simplicity. Configure it, run it, and let it handle the daily tasks in the background.

---

## 📋 Requirements

### Software
* Make sure you have **Python 3.9 or higher** installed on your system.
* **Pip** (Python's package installer) must be available.

### Testnet Funds
Before running the bot, ensure your wallets are funded with the necessary testnet tokens. Use the official faucets below:
* [**ETH Sepolia Faucet**](https://cloud.google.com/application/web3/faucet/ethereum/sepolia)
* [**ETH Holesky Faucet**](https://cloud.google.com/application/web3/faucet/ethereum/holesky)
* [**SEI Faucet**](https://docs.sei.io/learn/faucet)
* [**BTCN Faucet**](https://faucet.conduit.xyz/corn-testnet-l8rm17uloq)

---

## 🚀 Installation

Choose the installation method that best suits your needs.

### Option 1: Easy Install (One-Click)
This is the fastest way to get started. Run the single command below to download and execute the setup script.
```bash
wget https://raw.githubusercontent.com/airdropalc/Union-Auto-Swap/refs/heads/main/union.sh -O union.sh && chmod +x union.sh && ./union.sh
```

### Option 2: Manual Installation (Full Control)
This method is for users who prefer to review the code and configure files manually.

**1. Clone the Repository**
```bash
git clone https://github.com/airdropalc/Union-Auto-Swap.git
cd Union-Auto-Swap
```

**2. Install Dependencies**
```bash
# Use pip or pip3 depending on your system configuration
pip install -r requirements.txt
```

**3. Configure Accounts**
You must add your wallet private keys to the `accounts.json` file.
```bash
# Use your preferred text editor
nano accounts.json
```
**Example `accounts.json` format:**
```json
[
  {
    "account_name": "my_first_wallet",
    "private_key": "YOUR_WALLET_1_PRIVATE_KEY_HERE"
  },
  {
    "account_name": "another_wallet",
    "private_key": "YOUR_WALLET_2_PRIVATE_KEY_HERE"
  }
]
```

**4. Configure Proxies (Optional)**
If you want to use proxies, add them to `proxy.txt`, one per line.
```bash
nano proxy.txt
```

**5. Run the Bot**
```bash
python3 union.py
```
---

## ⚠️ Security Warning & Disclaimer

**This tool is for educational purposes only. Use it wisely and at your own risk.**

* **Handle Your Private Keys With Extreme Care:** The `accounts.json` file stores your private keys. Your private keys grant **complete control** over your wallets and funds. **Never share them or expose them in public repositories.**
* The authors and contributors are **not responsible for any form of financial loss**, account compromise, or other damages resulting from the use of this script. The security of your accounts is **your responsibility**.

---
> Inspired by and developed for the [Airdrop ALC](https://t.me/airdropalc) community.

## License

![Version](https://img.shields.io/badge/version-1.0.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

---
