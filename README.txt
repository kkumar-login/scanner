# 📡 Multi‑Chain Mnemonic Scanner (with Web Dashboard)

A high-speed, multi-threaded crypto wallet scanner that generates random 12-word mnemonic seed phrases and checks balances & NFTs across multiple blockchains. Includes a live web dashboard with real-time stats.

---

## ✅ Features

- 🧠 Generates random BIP39 12-word mnemonic phrases
- 🌐 Multi-chain support:
  - Ethereum (ETH)
  - Binance Smart Chain (BNB)
  - Polygon (MATIC)
  - Avalanche (AVAX)
  - Solana (SOL)
  - Bitcoin (BTC)
- 📦 Scans for both:
  - Native token balances
  - NFTs (ERC-721/ERC-1155 for EVM chains)
- 🖥️ Web dashboard:
  - Live stats: Checked, Speed (addr/sec), Recent results
  - Auto-refresh every 3 seconds
- 🎨 Terminal display:
  - Color-coded output per blockchain
  - Live update line (addr/sec)
- ⚙️ Threaded: 100 threads by default
- 🛑 Clean exit with `CTRL + C`

---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourrepo/mnemonic-scanner.git
cd mnemonic-scanner