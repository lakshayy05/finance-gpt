# 💚 FinanceGPT — AI Personal Finance Coach for India

<div align="center">

![FinanceGPT Banner](https://img.shields.io/badge/FinanceGPT-AI%20Finance%20Coach-22C55E?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTEgMTVoLTJ2LTZoMnY2em0wLThoLTJWN2gydjJ6Ii8+PC9zdmc+)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-finance--gpt--19.streamlit.app-22C55E?style=for-the-badge&logo=streamlit)](https://finance-gpt-19.streamlit.app)
[![Hugging Face](https://img.shields.io/badge/Model-HuggingFace-FFD21E?style=for-the-badge&logo=huggingface)](https://huggingface.co/lakshayyy19/FinanceGPT-Mistral-7B)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

**An end-to-end AI-powered personal finance platform built specifically for Indian salaried professionals aged 24–32.**

[**🚀 Try Live Demo**](https://finance-gpt-19.streamlit.app) • [**📖 API Docs**](https://financegpt-backend.onrender.com/docs) • [**🤗 Model**](https://huggingface.co/lakshayyy19/FinanceGPT-Mistral-7B)

</div>

---

## 🎯 Problem Statement

India has 300M+ middle-class salaried professionals. Most have **zero financial literacy**:

- Don't know what PPF, ELSS, NPS, or HRA is
- Never started a SIP (Systematic Investment Plan)
- Leaving ₹50,000+ in Section 80C tax savings unused every year
- Getting financial advice from Instagram reels
- Existing apps give generic global advice — not India-specific

**FinanceGPT talks to a 26-year-old Bangalore software engineer about HRA exemption, Nifty 50 index funds, and emergency fund planning — in simple, friendly language.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Finance Coach** | Fine-tuned Mistral 7B chatbot with full user profile context |
| 📊 **Financial Health Score** | 0-100 score based on savings rate, EF, investments, debt |
| 📂 **Bank Statement Parser** | Upload PDF → AI auto-categorises all transactions |
| 📈 **SIP Calculator** | Compound growth charts with year-by-year projections |
| 💰 **Tax Planner** | Old vs new regime comparison with slab-by-slab breakdown |
| 📋 **Budget Planner** | Set limits per category, AI suggests optimal budget |
| 🔔 **Spending Alerts** | Warnings when approaching or exceeding budget limits |
| 📅 **Weekly Report** | AI-generated personalised weekly spending summary |
| 🔴 **Live Market Data** | Real-time Nifty 50, Sensex, Gold, Silver prices |
| 🔐 **Auth + Persistence** | Supabase login — data saved across sessions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Browser)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────┐
│              FRONTEND — Streamlit                        │
│         finance-gpt-19.streamlit.app                     │
│  9 tabs: Dashboard | Budget | Alerts | Weekly Report     │
│          SIP Calc | Tax | Statement | Market | Chat      │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────┐
│              BACKEND — FastAPI                           │
│         financegpt-backend.onrender.com                  │
│  12 endpoints across 6 routers                          │
│  profile | chat | tools | market | budget | auth        │
└──────┬──────────────┬──────────────┬────────────────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌────▼────────────────────┐
│  AI Layer   │ │  Supabase │ │    Market Data           │
│             │ │           │ │                          │
│ Fine-tuned  │ │ PostgreSQL│ │  yfinance                │
│ Mistral 7B  │ │ Auth      │ │  Nifty 50, Sensex        │
│ (HuggingFace│ │ RLS       │ │  Gold, Silver            │
│  + Mistral  │ │ 5 tables  │ │  USD/INR                 │
│  API backup)│ │           │ │                          │
└─────────────┘ └───────────┘ └──────────────────────────┘
```

---

## 🧠 Fine-Tuned Model

The AI brain is **not a generic ChatGPT wrapper.** It's a Mistral 7B model fine-tuned specifically on Indian personal finance data.

### Training Details

| Parameter | Value |
|---|---|
| Base model | `mistralai/Mistral-7B-Instruct-v0.3` |
| Fine-tuning method | QLoRA (4-bit quantization) |
| Framework | Unsloth (2x faster training) |
| Hardware | Google Colab T4 GPU (free tier) |
| Dataset | 896 custom Indian finance Q&A pairs |
| Dataset source | Generated via Gemini 2.5 Flash API |
| Epochs | 3 |
| Final val loss | **0.3745** |

### Training Results

| Step | Training Loss | Validation Loss |
|---|---|---|
| 50 | 0.491 | 0.481 |
| 100 | 0.387 | 0.407 |
| 150 | 0.300 | 0.391 |
| 200 | 0.297 | 0.377 |
| 250 | 0.213 | 0.378 |
| 336 | **0.204** | **0.374** |

### Why Fine-Tuning Matters

```
Base Mistral 7B:           Fine-tuned FinanceGPT:
Generic global advice  →   India-specific (PPF/NPS/ELSS/80C)
"Invest in index funds" →  "Start ₹3,000/month Nifty 50 SIP
                            on Groww — here's the math..."
No Indian context      →   HRA, EPF, 80C, Groww, Zerodha
Generic responses      →   Uses your exact salary/expense numbers
```

---

## 🗂️ Project Structure

```
FinanceGPT/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── models.py                # Pydantic data models
│   ├── routes/
│   │   ├── auth.py              # POST /api/auth/signup, signin, profile
│   │   ├── profile.py           # POST /api/profile/analyse
│   │   ├── chat.py              # POST /api/chat
│   │   ├── tools.py             # SIP calc, tax calc, PDF parse
│   │   ├── market.py            # GET /api/market/prices
│   │   └── budget.py            # Budget, alerts, weekly report
│   └── services/
│       ├── ai.py                # HF model + Mistral fallback
│       ├── finance.py           # Health score, SIP math, tax calc
│       ├── parser.py            # PDF bank statement parser
│       └── database.py          # Supabase CRUD operations
├── frontend/
│   └── app.py                   # Streamlit UI (9 tabs)
├── dataset/
│   ├── generate_dataset.py      # Gemini API dataset generator
│   ├── validate_dataset.py      # Quality checker (87.8% score)
│   └── clean_dataset.py         # Encoding + quality fixes
├── .env                         # API keys (not committed)
└── requirements.txt
```

---

## 🚀 API Endpoints

```
GET  /api/health                 Health check
POST /api/auth/signup            Create account
POST /api/auth/signin            Login
POST /api/auth/profile/save      Save profile to Supabase
POST /api/auth/profile/load      Load profile on login
POST /api/profile/analyse        Full financial analysis
POST /api/chat                   AI chat (stateless)
POST /api/sip/calculate          SIP compound interest
POST /api/tax/calculate          Old vs new regime tax
POST /api/statement/parse        PDF bank statement parser
GET  /api/market/prices          Live Nifty/Gold/Silver
GET  /api/market/history/{sym}   Price history charts
POST /api/budget/analyse         Budget vs actual
POST /api/budget/suggest         AI budget recommendation
POST /api/budget/weekly-report   AI weekly summary
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, Plotly |
| Backend | FastAPI, Pydantic, Uvicorn |
| AI/ML | LangChain, Mistral API, HuggingFace |
| Fine-tuning | Unsloth, QLoRA, Google Colab T4 |
| Database | Supabase (PostgreSQL + Auth) |
| Market data | yfinance |
| PDF parsing | pdfplumber |
| Dataset gen | Gemini 2.5 Flash API |
| Deployment | Render (backend), Streamlit Cloud (frontend) |

---

## ⚙️ Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/lakshayy05/finance-gpt.git
cd finance-gpt
```

**2. Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file**
```
MISTRAL_API_KEY=your_mistral_key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
HF_TOKEN=hf_xxxx
HF_MODEL_URL=https://api-inference.huggingface.co/models/lakshayyy19/FinanceGPT-Mistral-7B-merged
BACKEND_URL=http://localhost:8000
```

**5. Run**
```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py
```

**6. Open** `http://localhost:8501`

---

## 📊 Dataset

The fine-tuning dataset was custom-generated using Gemini 2.5 Flash API:

- **896 examples** covering 50 Indian finance topics
- Each example has realistic Indian personas (name, city, age, salary in ₹)
- Step-by-step math with exact Indian numbers
- Topics: Emergency fund, SIP, 80C tax saving, HRA, PPF, NPS, ELSS, home loan, credit card debt, budgeting, gold investment, and 40+ more
- Quality score: **87.8%** (validated with custom script)
- Format: ChatML, Alpaca, Mistral instruct (3 formats saved)

---

## 🔮 Future Roadmap

- [ ] **Android app** with real-time SMS transaction reading
- [ ] **RAG integration** — RBI/SEBI documents for current regulatory info
- [ ] **Groww/Zerodha API** — deep-link to SIP setup directly from app
- [ ] **Weekly email nudges** — personalised spending alerts via cron job
- [ ] **More fine-tuning data** — edge cases (job loss, FIRE planning, windfall)
- [ ] **SEBI sandbox partnership** — for legal investment recommendations
- [ ] **React/Next.js frontend** — better mobile experience
- [ ] **Freemium model** — ₹99/month for advanced features

---

## 👨‍💻 Built By

**Lakshay** — Final year B.Tech, AI & Data Science, GGSIPU Delhi

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-lakshayyy19-FFD21E?style=flat&logo=huggingface)](https://huggingface.co/lakshayyy19)

---

## ⚠️ Disclaimer

FinanceGPT provides **financial education and planning tools only** — not SEBI-regulated investment advice. Always consult a qualified financial advisor before making investment decisions.

---

<div align="center">
  <strong>If this project helped you, please ⭐ star the repo!</strong>
</div>