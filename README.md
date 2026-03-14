# FairLance 🤝
### AI-Powered Autonomous Freelance Platform

> **Zero disputes. Zero manual oversight. Payments tied directly to verified work.**

FairLance is an AI agent that acts as an autonomous intermediary between employers and freelancers. It analyzes project requirements, breaks them into milestones, evaluates submitted work, manages escrow payments, and maintains a dynamic reputation score — all without human supervision.

---

## 🚀 Demo Flow

```
Employer posts project
        ↓
AI breaks it into milestones with payment splits
        ↓
Employer locks full budget in escrow
        ↓
Freelancer submits work for each milestone
        ↓
AI evaluates quality → COMPLETED / PARTIAL / FAILED
        ↓
Payment auto-released on approval
        ↓
PFI score updated automatically
```

---

## 🧠 AI Features

### 1. Milestone Generator
Takes a plain-English project description and budget, returns 3–5 structured milestones with:
- Clear completion criteria
- Payment percentage per milestone
- Deadline in days

### 2. Work Evaluator
Evaluates freelancer submissions against milestone criteria using:
- Python-based vague/incomplete detection (no AI hallucination)
- Criteria match scoring
- Evidence detection
- Client approval bonus
- Returns: `completed` / `partial` / `failed` with score and feedback

### 📋 Evaluator Response Guide

Use these sample submissions to test and demo the evaluator. Each one reliably triggers a specific verdict.

---

#### ✅ COMPLETED — Score 80–95

Paste this to get a **green COMPLETED** verdict:

```
I have completed the project planning and concept phase. Here is what I delivered:

- Written project plan document covering timeline, deliverables, and tech stack
- Visual mood board with 3 design directions created in Figma
- Color palette and typography choices finalized
- Client has reviewed and approved the mood board via email on Day 1
- All assets shared in a Google Drive folder with client access confirmed
```

**Why it passes:** Directly addresses all criteria, includes evidence (Figma, Drive link), and mentions client approval.

---

#### ⚠️ PARTIAL — Score 40–75

Paste this to get a **yellow PARTIAL** verdict:

```
I have created wireframes for all 5 pages of the website and designed
the homepage layout with a hero section. I chose a blue and white color
scheme and have shared the Figma file. However, I am still waiting for
the client to review and approve the designs. I expect approval within
the next 24 hours.
```

**Why it's partial:** Work is done and evidence is provided, but client approval is still pending — a key criteria point is unmet.

---

#### ❌ FAILED — Score 0–25

Paste this to get a **red FAILED** verdict:

```
I started working on it but haven't finished yet. Will submit soon.
```

**Why it fails:** Python detects "haven't" and "will submit" as incomplete phrases before the AI is even called. Hard capped at score 15.

Also triggers FAILED:

```
Almost done, will send the files later today.
```

```
Not ready yet, still working on it.
```

---

#### 🔢 How Scoring Works

| Condition | Effect on Score |
|-----------|----------------|
| Contains "will do", "not finished", "haven't", "soon", etc. | Hard cap → **15** (Python, before AI) |
| Submission under 80 characters | Hard cap → **20** (Python, before AI) |
| All criteria explicitly proven + evidence | **85–95** |
| Most criteria met, no evidence | **× 0.55 penalty** |
| Client approval confirmed | **+10 bonus** |
| Some criteria missing | **40–75 range** |

---

### 3. Professional Fidelity Index (PFI)
AI-calculated reputation score built from:
- **Milestone Accuracy** (40% weight) — how often work is fully completed
- **Deadline Adherence** (30% weight) — how often deadlines are met
- **Work Quality** (30% weight) — average score across all submissions

```
PFI = (Milestone Accuracy × 0.4) + (Deadline Adherence × 0.3) + (Work Quality × 0.3)
```

Grades: A (80–100) · B (65–79) · C (50–64) · D (35–49) · F (below 35)

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Groq API — `llama-3.3-70b-versatile` |
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite |
| Frontend | HTML · CSS · Vanilla JavaScript |
| Fonts | Syne + DM Sans (Google Fonts) |

---

## 📁 Project Structure

```
FairLance/
├── API/
│   ├── main.py          # FastAPI server — all endpoints
│   ├── ai_agent.py      # AI functions (milestones, evaluate, PFI)
│   ├── models.py        # SQLAlchemy database models
│   ├── database.py      # DB connection and session
│   └── fairlance.db     # SQLite database (auto-created)
│
├── Frontend/
│   ├── index.html       # Homepage
│   ├── login.html       # Role-based login (Employer / Freelancer)
│   ├── employer.html    # Post project + AI milestone generation
│   ├── freelancer.html  # Browse projects + submit work + AI verdict
│   ├── profile.html     # PFI score dashboard
│   └── nav-guard.js     # Role-based navigation protection
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/AbhinavVijayvergia/FairLance.git
cd FairLance
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key
Open `API/ai_agent.py` and replace the API key:
```python
client = Groq(api_key="YOUR_GROQ_API_KEY_HERE")
```

### 4. Start the backend server
```bash
cd API
python -m uvicorn main:app --reload
```
Server runs at: `http://127.0.0.1:8000`
API docs at: `http://127.0.0.1:8000/docs`

### 5. Open the frontend
Open `Frontend/index.html` in your browser. All pages connect to the backend automatically.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/project/create` | Create a new project |
| `POST` | `/project/create-with-milestones` | Create project + AI generates milestones |
| `POST` | `/project/create-from-milestones` | Save project with pre-generated milestones |
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}/milestones` | Get milestones for a project |
| `POST` | `/ai/generate-milestones` | AI milestone generation only |
| `POST` | `/milestone/submit` | Submit work for a milestone |
| `POST` | `/verify/work` | AI evaluates submitted work |
| `GET` | `/pfi/{freelancer_id}` | Get PFI profile for a freelancer |
| `POST` | `/pfi/calculate` | Calculate PFI from custom history |

---

## 👤 Role-Based Access

| Feature | Employer | Freelancer |
|---------|----------|------------|
| Post Projects | ✅ | ❌ |
| Generate AI Milestones | ✅ | ❌ |
| Browse Projects | ❌ | ✅ |
| Submit Work | ❌ | ✅ |
| AI Work Evaluation | ❌ | ✅ |
| View PFI Score | ✅ | ✅ |

---

## 💡 Why FairLance?

Traditional freelance platforms suffer from:
- **Biased reviews** — easy to fake, hard to verify
- **Payment disputes** — manual resolution takes days
- **No objective quality standard** — subjective employer ratings

FairLance solves this by replacing human judgment with:
- ✅ AI-evaluated completion criteria
- ✅ Automated escrow release
- ✅ Tamper-proof PFI scoring
- ✅ Zero manual oversight

---

## 🛠️ Requirements

```
fastapi
uvicorn
sqlalchemy
pydantic
groq
```

Install all with:
```bash
pip install fastapi uvicorn sqlalchemy pydantic groq
```

---

## 👨‍💻 Built At

Built during a 32-hour hackathon.

---

## ⚠️ Important Notes

- Never commit your Groq API key to GitHub
- The SQLite database (`fairlance.db`) is auto-created on first run
- Always start the backend server before opening the frontend
- Run uvicorn from inside the `API/` folder to avoid database path issues
