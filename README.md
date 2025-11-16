# HORUS: FULLY DECENTRALIZED BLOCKCHAIN + AI ANOMALY DETECTION SYSTEM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Decentralized](https://img.shields.io/badge/System-Fully%20Decentralized-blue)](#)
[![AI Engine](https://img.shields.io/badge/AI-Anomaly%20Detection-green)](#)
[![Blockchain](https://img.shields.io/badge/Blockchain-Immutable%20Audit-red)](#)

HORUS adalah sistem deteksi anomali transaksi berbasis **blockchain** dan **AI** yang sepenuhnya **tanpa pusat**. Setiap transaksi dianalisis sebelum atau sesudah masuk ke jaringan, dan hasil deteksi dicatat secara on-chain untuk memastikan integritas, auditabilitas, dan transparansi yang tidak dapat dimanipulasi.

---

## FITUR UTAMA

* **AI-BASED ANOMALY DETECTION** – Model machine learning untuk deteksi transaksi tidak wajar.
* **FULLY DECENTRALIZED** – Tidak ada server pusat, komunikasi menggunakan P2P.
* **ON-CHAIN RECORDING** – Semua flag anomali dicatat di smart contract.
* **IMMUTABLE AUDIT LOGS** – Catatan permanen untuk pemerintahan, publik, dan auditor.
* **IPFS ENCRYPTED STORAGE** – Payload besar disimpan terdistribusi.
* **GOVERNANCE & VALIDATION** – Mekanisme kontrol berbasis smart contract.

---

## ARSITEKTUR SISTEM

```
┌────────────────────────────┐
│        CLIENT / UI          │
│ (Dashboard / Submission)    │
└──────────────┬─────────────┘
               │
               ▼
     ┌──────────────────────────────┐
     │        P2P NODES (libp2p)     │
     │  Discovery / Validate / Sync  │
     └──────────────┬───────────────┘
                    │
      ┌─────────────┴──────────────┐
      │                            │
      ▼                            ▼
┌───────────────────┐     ┌────────────────────────┐
│ SMART CONTRACTS    │     │ IPFS ENCRYPTED STORAGE │
│ (EVM Compatible)   │     │     (CID Based)        │
└───────────┬────────┘     └──────────────┬────────┘
            │                              │
            ▼                              ▼
     ┌────────────────────────────────────────────┐
     │    AI ANOMALY DETECTION ENGINE (FastAPI)   │
     │   Autoencoder / Isolation Forest / Hybrid   │
     └────────────────────────────────────────────┘
```

---

## STRUKTUR DIREKTORI

```
horus-project/
│
├── CONTRACTS/                  # Smart Contract Solidity
│   ├── SCRIPTS/
│   ├── TEST/
│   └── HARDHAT.CONFIG.JS
│
├── NODE/                       # Node P2P libp2p
│   ├── SRC/
│   ├── CONFIG/
│   └── DOCKERFILE
│
├── INFERENCE/                  # AI Model + API FastAPI
│   ├── API/
│   ├── MODEL/
│   ├── NOTEBOOKS/
│   └── REQUIREMENTS.TXT
│
├── WEB-UI/                     # Dashboard / UI
├── SCRIPTS/                    # Deployment tools
└── README.MD
```

---

## QUICK START

### PREREQUISITES

* Node.js v18+
* Python 3.10+
* Docker / Docker Compose
* Wallet blockchain sesuai jaringan

### 1. CLONE REPOSITORY

```bash
git clone https://github.com/laudzakusuma/horus-project.git
cd horus-project
```

### 2. JALANKAN IPFS

```bash
docker run -d --name ipfs_host \
 -v ipfs_data:/data/ipfs \
 -p 5001:5001 -p 8080:8080 \
 ipfs/go-ipfs:latest
```

### 3. JALANKAN BLOCKCHAIN LOCAL (HARDHAT)

```bash
cd contracts
npm install
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

### 4. JALANKAN P2P NODE

```bash
cd node
npm install
npm run build
npm run start:dev
```

### 5. JALANKAN AI INFERENCE ENGINE

```bash
cd inference
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## ENVIRONMENT VARIABLES

```
# Blockchain
RPC_URL=http://localhost:8545
CHAIN_ID=1337

# Smart Contract
CONTRACT_ADDRESS=your_contract_address

# AI Engine
AI_API_URL=http://localhost:8000/score

# IPFS
IPFS_API=http://localhost:5001
```

---

## TEKNOLOGI UTAMA

### SMART CONTRACTS

* Solidity
* Hardhat
* EVM Compatible
* OpenZeppelin Libraries

### AI & BACKEND

* Python FastAPI
* PyTorch / Scikit-learn
* Model: Autoencoder / Isolation Forest

### P2P LAYER

* libp2p (peer discovery, routing, messaging)

### STORAGE

* IPFS (CID-based encrypted files)

### FRONTEND

* Next.js / React
* Tailwind / Styled Components

---

## THREAT / ANOMALY CATEGORY (RECOMMENDED)

1. SUSPICIOUS_AMOUNT
2. UNUSUAL_FREQUENCY
3. BLACKLISTED_ENTITY
4. GEOLOCATION_MISMATCH
5. MULTI-ACCOUNT_PATTERN
6. STRUCTURED_TRANSACTIONS
7. HIGH_RISK_SCORE
8. MODEL_OUTLIER_DETECTION

---

## CONTOH DETEKSI

```
Analyzing Transaction: 0xaf12...39a1
Amount: 12,300
Risk Score: 0.89
Anomaly: TRUE
Flag submitted to blockchain...
Transaction Hash: 0x91bcf...
Block Confirmed.
```

---

## EVENT SMART CONTRACT

```solidity
event AnomalyDetected(
    uint256 indexed id,
    bytes32 indexed txHash,
    address indexed account,
    uint256 score,
    bool isAnomaly,
    uint256 timestamp
);
```

---

## KONTRAK DEPLOY (CONTOH)

* Localhost: `0x0000000000000000000000000000000000000000`
* Explorer: gunakan Hardhat local explorer atau jaringan tujuan

---

## CONTRIBUTING

1. Fork repository
2. Buat branch baru (`feature/new-module`)
3. Commit perubahan (`git commit -m "Add new module"`)
4. Push dan ajukan Pull Request

---

## LICENSE

MIT (lihat file LICENSE)

---

## DISCLAIMER

HORUS adalah proof-of-concept. Penggunaan untuk produksi memerlukan audit tambahan, pengujian keamanan, dan verifikasi formal.
