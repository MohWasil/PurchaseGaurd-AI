# 🛡️ PurchaseGuard AI

> **Personal Receipt & Warranty Intelligence Agent** - Track purchases, monitor return deadlines, and protect your warranty claims with AI-powered automation.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [What This Project Solves](#-what-this-project-solves)
- [Features](#-features)
- [What It Does NOT Do](#-what-it-does-not-do)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Limitations & Known Issues](#-limitations--known-issues)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 What This Project Solves

Most people lose **hundreds of dollars yearly** due to:

| Problem | Impact |
|---------|--------|
| ❌ Lost or forgotten receipts | Cannot return defective items |
| ❌ Missed return deadlines (30-90 days) | Lose money on unwanted purchases |
| ❌ Expired warranties unnoticed | Pay for repairs that should be free |
| ❌ Scattered receipt data (email, paper, photos) | No centralized tracking |

**PurchaseGuard AI** automatically:
1. 📸 Scans receipt images using OCR
2. 🤖 Extracts merchant, date, amount using AI
3. ⏰ Calculates return deadlines & warranty expiry
4. 🔔 Sends alerts before deadlines expire
5. 📊 Provides dashboard for all purchase tracking

---

## ✨ Features

### ✅ Working Features

| Feature | Status | Details |
|---------|--------|---------|
| User Authentication | ✅ Working | JWT-based login/register |
| Receipt Upload | ✅ Working | PNG, JPG, JPEG up to 10MB |
| OCR Text Extraction | ✅ Working | Tesseract (free, offline) |
| AI Data Extraction | ✅ Working | Hugging Face LLM + regex fallback |
| Deadline Calculation | ✅ Working | Return window & warranty expiry |
| Dashboard Analytics | ✅ Working | Stats, charts, purchase list |
| Email Alerts | ⚠️ Optional | Requires Gmail SMTP config |
| CSV Export | ✅ Working | Download all purchases |
| Data Encryption | ✅ Working | AES-256 for sensitive data |

### 🔄 Planned Features

| Feature | Status | Notes |
|---------|--------|-------|
| Gmail Auto-Scan | 🔜 Planned | Requires Google OAuth setup |
| Price Tracking | 🔜 Planned | Needs external price API |
| Mobile App | 🔜 Planned | Future consideration |
| Multi-language OCR | 🔜 Planned | Currently English only |

---

## ⚠️ What It Does NOT Do

**Being transparent about limitations:**

| Claim | Reality |
|-------|---------|
| ❌ "100% accurate OCR" | OCR accuracy depends on image quality (70-95%) |
| ❌ "Works with all receipt formats" | Some receipt formats may not parse correctly |
| ❌ "Automatic email scanning" | Manual upload only (Gmail API not included) |
| ❌ "Price drop alerts" | Not implemented in current version |
| ❌ "Cloud storage" | All data stored locally on your machine |
| ❌ "Mobile app" | Web-based only (Streamlit) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PURCHASEGUARD AI                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐         ┌──────────────────┐                  │
│  │   STREAMLIT      │         │     FASTAPI      │                  │
│  │   FRONTEND       │◄───────►│     BACKEND      │                  │
│  │   (Port 8501)    │  HTTP   │     (Port 8000)  │                  │
│  └──────────────────┘         └──────────────────┘                  │
│         │                            │                               │
│         │                            │                               │
│         ▼                            ▼                               │
│  ┌──────────────────┐         ┌──────────────────┐                  │
│  │   User Interface │         │   AI Agent Core  │                  │
│  │   - Dashboard    │         │   - LangGraph    │                  │
│  │   - Upload       │         │   - HuggingFace  │                  │
│  │   - Alerts       │         │   - Tesseract    │                  │
│  └──────────────────┘         └──────────────────┘                  │
│                                      │                               │
│                                      ▼                               │
│  ┌──────────────────────────────────────────────────┐               │
│  │              DATA LAYER                          │               │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │               │
│  │  │   SQLite    │  │   Receipt   │  │  Alerts  │ │               │
│  │  │  Database   │  │   Files     │  │  Queue   │ │               │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────►│     OCR     │────►│  AI Extract │
│   Receipt   │     │  (Tesseract)│     │  (LLM/Regex)│
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Alert     │◄────│   Store     │◄────│  Calculate  │
│   User      │     │   Policy    │     │  Deadlines  │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Backend** | Python 3.11 + FastAPI | Fast, async, auto-docs |
| **Frontend** | Streamlit | Rapid development, no frontend expertise needed |
| **Database** | SQLite (async) | Zero config, file-based, portable |
| **AI/LLM** | Hugging Face (free tier) | No cost, good enough for receipt data |
| **OCR** | Tesseract | Free, offline, no API dependency |
| **Agent** | LangGraph + LangChain | Stateful workflows, easy to extend |
| **Auth** | JWT + bcrypt | Industry standard, secure |
| **Encryption** | AES-256 (Fernet) | Protects sensitive receipt data |
| **Scheduler** | APScheduler | Background deadline checking |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows 10/11 (tested), Linux/Mac should work
- Tesseract OCR installed
- Git (for cloning)

### Step 1: Install Tesseract OCR

**Windows:**
```bash
# Download installer from:
https://github.com/UB-Mannheim/tesseract/wiki

# Install to default location:
C:\Program Files\Tesseract-OCR

# Verify installation:
tesseract --version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/purchaseguard-ai.git
cd purchaseguard-ai
```

### Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env with your settings (see Configuration section)
```

### Step 5: Run Backend

```bash
python run.py
```

Backend will start at: `http://localhost:8000`

### Step 6: Run Frontend (New Terminal)

```bash
cd frontend

# Activate same virtual environment
..\backend\venv\Scripts\Activate

# Run Streamlit
streamlit run app.py
```

Frontend will start at: `http://localhost:8501`

### Step 7: Create Account & Upload

1. Open `http://localhost:8501` in browser
2. Click "Register" tab
3. Create account with email & password
4. Login with credentials
5. Go to "Upload Receipt" page
6. Upload receipt image (PNG, JPG, JPEG)
7. Wait for AI processing (10-30 seconds)
8. View results in Dashboard

---

## ⚙️ Configuration

### Required (.env)

```env
# Security (CHANGE THESE!)
SECRET_KEY=your-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/purchaseguard.db

# Encryption (32 bytes)
ENCRYPTION_KEY=your-random-32-byte-key-here

# OCR
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=eng

# Hugging Face (Optional but recommended)
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_your_free_token_here
HF_MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
```

### Optional (Email Alerts)

```env
# Gmail App Password (not regular password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=your-email@gmail.com
SEND_EMAIL_ALERTS=true
ALERT_CHECK_INTERVAL_HOURS=24
```

> **Get Gmail App Password:**
> 1. Enable 2FA on Google Account
> 2. Go to https://myaccount.google.com/apppasswords
> 3. Create app password for "Mail"
> 4. Copy 16-character password to `.env`

### Generate Secure Keys

```python
# Run this to generate secure keys
import secrets

print("SECRET_KEY:", secrets.token_urlsafe(32))
print("ENCRYPTION_KEY:", secrets.token_urlsafe(32))
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | ❌ |
| POST | `/api/v1/auth/login` | Login & get token | ❌ |
| GET | `/api/v1/auth/me` | Get current user | ✅ |
| POST | `/api/v1/purchases/upload` | Upload receipt | ✅ |
| GET | `/api/v1/purchases/` | Get all purchases | ✅ |
| GET | `/api/v1/purchases/{id}` | Get single purchase | ✅ |
| GET | `/api/v1/purchases/stats` | Get dashboard stats | ✅ |
| GET | `/api/v1/purchases/alerts` | Get all alerts | ✅ |
| GET | `/api/v1/purchases/export/csv` | Export to CSV | ✅ |
| DELETE | `/api/v1/purchases/{id}` | Delete purchase | ✅ |
| PATCH | `/api/v1/purchases/{id}/return` | Mark as returned | ✅ |
| PATCH | `/api/v1/purchases/{id}/claim` | Mark as claimed | ✅ |

**API Documentation:** `http://localhost:8000/docs`

---

## 📁 Project Structure

```
purchaseguard-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py        # SQLAlchemy models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   └── purchases.py     # Purchase endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT, encryption
│   │   │   ├── database.py      # DB connection
│   │   │   ├── ocr_service.py   # Tesseract OCR
│   │   │   ├── llm_service.py   # Hugging Face LLM
│   │   │   ├── email_service.py # SMTP email
│   │   │   └── scheduler.py     # Background tasks
│   │   └── agents/
│   │       ├── __init__.py
│   │       └── receipt_agent.py # LangGraph agent
│   ├── data/
│   │   ├── receipts/            # Stored receipt images
│   │   └── encrypted/           # Encrypted data
│   ├── venv/                    # Virtual environment
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── app.py                   # Streamlit application
├── .env                         # Environment variables
├── .gitignore
└── README.md
```

---

## 🔒 Security

### Implemented Security Measures

| Measure | Implementation | Status |
|---------|---------------|--------|
| Password Hashing | bcrypt | ✅ |
| JWT Authentication | python-jose | ✅ |
| Data Encryption | AES-256 (Fernet) | ✅ |
| Input Validation | Pydantic | ✅ |
| CORS Protection | FastAPI middleware | ✅ |
| File Type Validation | Extension check | ✅ |
| File Size Limit | 10MB max | ✅ |
| SQL Injection Prevention | SQLAlchemy ORM | ✅ |

### Security Considerations

| Risk | Mitigation |
|------|------------|
| Receipt images stored locally | Encrypt sensitive extracted data |
| API keys in .env file | Never commit .env to git |
| JWT tokens | 30-minute expiration |
| User data isolation | User ID on every query |

### What's NOT Secured (Production)

| Issue | Recommendation |
|-------|---------------|
| SQLite database | Use PostgreSQL for production |
| No rate limiting | Add Redis + rate limiter |
| No HTTPS (localhost) | Use reverse proxy with SSL |
| No backup system | Implement automated backups |

---

## ⚠️ Limitations & Known Issues

### OCR Accuracy

| Condition | Expected Accuracy |
|-----------|-------------------|
| Clear, flat receipt photo | 90-95% |
| Crumpled or wrinkled | 60-80% |
| Low light or blurry | 40-60% |
| Handwritten receipts | 20-40% |

**Tips for best results:**
- Take photos in good lighting
- Keep receipt flat on surface
- Ensure all text is visible
- Avoid shadows and glare

### Hugging Face Free Tier

| Limit | Value |
|-------|-------|
| Requests per minute | 5 |
| Requests per month | ~10,000 |
| Model availability | May vary |

**If rate limited:** System falls back to regex extraction (less accurate but functional)

### Known Issues

| Issue | Workaround |
|-------|------------|
| Date format parsing varies | Manual correction in dashboard |
| Some merchants not recognized | Edit manually after upload |
| Email alerts require Gmail | Use app password, not regular password |
| No mobile app | Use mobile browser (responsive) |

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### How to Contribute

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Add docstrings to functions
- Include tests for new features
- Update documentation as needed

### Issues to Help With

- [ ] Improve OCR accuracy for non-English receipts
- [ ] Add Gmail API integration
- [ ] Implement price tracking
- [ ] Add PostgreSQL support
- [ ] Create mobile-responsive frontend

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### What You Can Do

- ✅ Use for personal projects
- ✅ Use for commercial projects
- ✅ Modify and distribute
- ✅ Use in production

### What You Cannot Do

- ❌ Hold authors liable for damages
- ❌ Claim as your own original work

---

## 📞 Support

| Issue Type | Where to Get Help |
|------------|-------------------|
| Bug Reports | GitHub Issues |
| Feature Requests | GitHub Issues |
| General Questions | GitHub Discussions |
| Security Issues | Email maintainer directly |

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Streamlit](https://streamlit.io/) - Rapid frontend development
- [LangChain](https://langchain.com/) - AI agent framework
- [Hugging Face](https://huggingface.co/) - Free LLM access
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Lines of Code | ~2,500 |
| API Endpoints | 12 |
| AI Agent Nodes | 5 |
| Database Tables | 3 |
| Build Time (MVP) | 24 hours |
| Cost to Run | $0 (all free tools) |

---

## 🗺️ Roadmap

### Phase 1 (Completed ✅)
- [x] User authentication
- [x] Receipt upload
- [x] OCR extraction
- [x] AI data parsing
- [x] Dashboard display

### Phase 2 (Completed ✅)
- [x] Deadline calculation
- [x] Alert system
- [x] Email notifications
- [x] CSV export
- [x] Stats & charts

### Phase 3 (Planned 🔜)
- [ ] Gmail auto-scan integration
- [ ] Price tracking API
- [ ] PostgreSQL support
- [ ] Docker deployment
- [ ] Unit tests (80%+ coverage)

### Phase 4 (Future 🚀)
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Cloud storage option
- [ ] Browser extension

---

## ⚡ Quick Commands Reference

```bash
# Start backend
cd backend && .\venv\Scripts\Activate && python run.py

# Start frontend (new terminal)
cd frontend && ..\backend\venv\Scripts\Activate && streamlit run app.py

# Install new dependency
pip install package-name >> requirements.txt

# Clear Python cache
del /s /q *.pyc && rmdir /s /q __pycache__

# Check API health
curl http://localhost:8000/api/v1/health

# View API docs
open http://localhost:8000/docs
```

---

<div align="center">

**Built with ❤️ using 100% free tools**

[Report Bug](https://github.com/MohWasil/PurchaseGaurd-AI/tree/main) · [Request Feature](https://github.com/MohWasil/PurchaseGaurd-AI/tree/main)

</div>