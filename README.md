# Customer Health Forensics

## Turn customer behavior data into retention intelligence — before customers leave

> An end-to-end ML system that combines churn prediction, consensus XAI, behavioral segmentation, drift detection, and LLM-generated insights into one unified customer intelligence platform.

---

## What Is This System?

Customer Health Forensics is a full-stack, production-grade churn intelligence platform built across 8 sequential phases. It processes 500,000+ customer records, trains and explains a churn prediction model, segments customers by behavioral degradation, detects early warning signals through drift analysis, and generates executive-grade business intelligence — all accessible through a React dashboard backed by a FastAPI REST API.

This is not a dashboard with charts. It is a **decision-making system** that tells you:

- **WHAT** is happening with your customers
- **WHY** it is happening (causal analysis)
- **WHAT WILL happen** if no action is taken (predictive outlook)
- **WHAT TO DO** (prioritized, RL-optimized recommendations)

---

## The Problem

SaaS businesses lose 5–15% of their customer base every month to churn. The companies that survive are the ones that see it coming. The companies that fail are the ones that notice after renewal dates pass.

Most churn is **predictable 4–8 weeks in advance** if you know where to look.

---

## Why Existing Solutions Fail

| Tool | What it does | What it misses |
| ------ | ------------- | ---------------- |
| Mixpanel / Amplitude | Track events | Can't predict who will leave |
| Salesforce Health Score | Weighted rule score | No statistical validation, no causality |
| Black-box ML | Predicts churn | No explainability, no trust |
| Single-method XAI (SHAP only) | Explains predictions | Unreliable — one method can be wrong |
| BI dashboards | Show current state | No drift detection, no early warnings |

The gap is **causal, explainable, early-warning intelligence** — not just prediction.

---

## What This System Solves

1. **Prediction** — Trains XGBoost/Logistic models on 12-month behavioral snapshots, achieving AUC 0.9273 on 500K customers.

2. **Consensus XAI** — Uses SHAP (primary) + LIME + AIX360 (validators). Only labels a feature explanation HIGH confidence when all three methods agree on direction and rank. No single-method trust.

3. **Temporal Segmentation** — Detects not just which segment is bad, but which is *getting worse* — identifying accelerating risk before it spikes.

4. **Drift Detection + Early Warning** — PSI + KS-test identifies which behavioral features are shifting. Features that are (a) drifting AND (b) XAI-confirmed churn drivers → flagged as early warning signals 4–6 weeks before churn spikes.

5. **LLM Intelligence Layer** — Generates executive summaries, causal chains, predictive outlooks, and prioritized recommendations. Falls back to deterministic rule engine when LLM unavailable.

6. **Full API + Dashboard** — Everything accessible via FastAPI REST API and a React dashboard with real-time exploration, side panel deep-dives, and export capabilities.

---

## Key Features

### Churn Prediction

- Size-aware model selection: XGBoost vs Logistic Regression
- Stratified 70/10/20 train/val/test split
- SMOTE balancing for class imbalance
- 12 engineered features including stickiness index, payment risk, NPS band, health score

### Consensus XAI

- Agreement-based confidence: HIGH requires all 3 methods to agree
- Direction tracking (risk+ / risk-) per feature per customer
- Global population-level and per-customer local explanations
- Watchlist: top 200 Critical-tier customers with full reasoning

### Segmentation Intelligence

- 5 dimensions: plan_type, region, contract_type, behavior_tier, NPS band
- Temporal degradation tracking across 12 months
- Acceleration detection: segments consistently worsening across periods
- Revenue at risk calculated per segment (annualized)
- PostgreSQL storage with 12 named analytical queries

### Drift Detection

- PSI (Population Stability Index) for distribution magnitude
- KS-test for statistical significance
- Combined assessment: confirmed drift = PSI ≥ 0.10 AND KS p < 0.05
- R cross-validation: independent statistical verification
- Octave mathematical validation: PSI cross-check + KL divergence
- Automatic retraining trigger when PSI > 0.20 on 3+ features

### Insight Engine

- 15 deterministic rules covering engagement, payment, support, satisfaction, contract
- ANN (sklearn MLP 64→32) for feature impact scoring and interaction detection
- Q-learning RL recommender with 12 retention actions and experience replay
- LangChain + HuggingFace (Mistral-7B) with full rule-based fallback
- Natural language Q&A with 16 intent patterns

### FastAPI Backend

- 20+ REST endpoints
- Role-based auth (admin / read_only) via API key
- Async SQLAlchemy with PostgreSQL (prod) / SQLite (dev)
- Background pipeline execution for uploads
- PDF and Excel report generation

### React Dashboard

- Dual-mode: Demo (instant) and Live Analysis (upload your data)
- Dark AI theme with risk-coded color system
- Animated pipeline visualization on landing
- Slide-in RightPanel for deep-dive on any element
- Full Recharts data visualization suite

---

## System Architecture

``` bash
┌─────────────────────────────────────────────────────────┐
│                   DATA LAYER (Phase 1)                  │
│  500K customers · 12-month snapshots · 12 features      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    ML LAYER (Phase 1)                   │
│  XGBoost + Logistic · AUC 0.9273 · Size-aware selection │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   XAI LAYER (Phase 2)                   │
│  SHAP (primary) + LIME + AIX360 · Agreement-based conf  │
└──────────┬───────────────────────────────┬──────────────┘
           │                               │
┌──────────▼──────────┐       ┌────────────▼──────────────┐
│ SEGMENTATION        │       │ DRIFT DETECTION (Phase 4) │
│ (Phase 3)           │       │ PSI + KS + R + Octave     │
│ Python+SQL+R        │       │ Early warning signals     │
└──────────┬──────────┘       └────────────┬──────────────┘
           │                               │
┌──────────▼───────────────────────────────▼──────────────┐
│                  INSIGHT LAYER (Phase 5)                │
│  Rules + ANN + RL + LLM → WHAT/WHY/NEXT/ACTION         │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  API LAYER (Phase 6)                    │
│  FastAPI · 20+ endpoints · PostgreSQL · Auth            │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                DASHBOARD (Phase 7)                      │
│  React 18 · TypeScript · Framer Motion · Recharts       │
└─────────────────────────────────────────────────────────┘
```

---

## End-to-End Workflow

``` bash
1. Upload CSV/Excel or connect PostgreSQL/SQLite
         ↓
2. Data validation + feature engineering (12 features)
         ↓
3. Model training + XAI-coupled selection
         ↓
4. Consensus XAI → per-customer explanations + watchlist
         ↓
5. Segmentation → 5 dimensions × temporal degradation
         ↓
6. Drift detection → PSI + KS + early warning flags
         ↓
7. Insight generation → 8-section intelligence report
         ↓
8. Dashboard → exploration, deep-dive, export
```

---

## Tech Stack by Phase

| Phase | Tools |
| ------- | ------- |
| 1 Data + ML | Python, pandas, scikit-learn, XGBoost, joblib |
| 2 XAI | SHAP, LIME, AIX360, Python |
| 3 Segmentation | Python, PostgreSQL, R (ANOVA/Tukey), openpyxl |
| 4 Drift | Python, SciPy, R (KS/Spearman), GNU Octave |
| 5 Insights | Python, sklearn MLP, LangChain, HuggingFace, Jinja2 |
| 6 Backend | FastAPI, Uvicorn, SQLAlchemy async, Pydantic v2 |
| 7 Frontend | TypeScript, React 18, Vite, Tailwind CSS, Recharts, Framer Motion |
| 8 Deploy | Docker, Docker Compose, GitHub Actions, Render |

---

## Project Structure

```bash
customer_health_forensics/
├── src/                     # All Phase 1–5 Python source
│   ├── data_generator.py
│   ├── feature_engineering.py
│   ├── model_selector.py
│   ├── pipeline.py
│   ├── xai_engine.py
│   ├── reasoning_layer.py
│   ├── xai_runner.py
│   ├── segmentation_engine.py
│   ├── cohort_analysis.py
│   ├── psi.py
│   ├── ks_test.py
│   ├── drift_engine.py
│   ├── rule_engine.py
│   ├── ann_feature_model.py
│   ├── rl_recommender.py
│   ├── reasoning_engine.py
│   ├── prompt_templates.py
│   ├── llm_pipeline.py
│   ├── insight_engine.py
│   ├── qa_engine.py
│   ├── api/routes/          # FastAPI route handlers
│   ├── core/                # Config, database, security
│   ├── db/                  # ORM models + CRUD
│   ├── services/            # Business logic delegation
│   ├── schemas/             # Pydantic request/response models
│   └── utils/               # Logger, file handler, background tasks
├── backend/
│   ├── Dockerfile
│   └── requirements.txt
├── Frontend/
│   └── src/                 # React TypeScript application
├── sql/                     # PostgreSQL schema + queries
├── r/                       # R statistical validation scripts
├── octave/                  # Octave mathematical validation
├── notebooks/               # Colab notebooks (Phases 1–5)
├── docker-compose.yml
├── train.py                 # CLI: train model
├── test.py                  # CLI: evaluate model
├── insight_runner.py        # CLI: generate insights + Q&A
├── run_full_pipeline.py     # CLI: full Phase 3+4 pipeline
└── requirements.txt
```

---

## System Outputs

| Output | Location | Description |
| -------- | ---------- | ------------- |
| Trained model | `models/best_model.pkl` | XGBoost/Logistic + feature pipeline |
| Leaderboard | `models/leaderboard.csv` | All models + AUC/F1 |
| XAI global | `outputs/xai/global_explanation.json` | Population feature importance |
| Watchlist | `outputs/xai/watchlist_reasoning.json` | Top 200 critical customers + WHAT/WHY |
| Segments | `outputs/segmentation/segment_results.json` | All segments + temporal metrics |
| Drift report | `outputs/drift/drift_report.json` | PSI + KS + early warnings |
| Intelligence | `outputs/insights/intelligence_report.json` | 8-section executive report |
| RL policy | `outputs/insights/rl_policy.json` | Learned retention actions |
| Excel cohort | `outputs/reports/cohort_report_*.xlsx` | Formatted cohort workbook |
| Executive PDF | `outputs/reports/executive_report_*.pdf` | Board-ready PDF |

---

## Installation Guide (Local)

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### Step 1 — Clone and Python setup

```bash
git clone https://github.com/your-org/customer_health_forensics.git
cd customer_health_forensics
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Environment

```bash
cp .env.example .env
# Edit .env with your values (API keys at minimum)
```

### Step 3 — Run the ML pipeline

```bash
# Generate data + train model (takes ~5 min on local machine)
python train.py

# Evaluate model
python test.py

# Run XAI (Phase 2)
python xai_run.py

# Run segmentation + drift (Phase 3+4)
python run_full_pipeline.py --skip-db --skip-r --skip-octave

# Generate insights (Phase 5)
python insight_runner.py
```

### Step 4 — Start the backend

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
# API docs at: http://localhost:3000/docs
```

### Step 5 — Start the frontend

```bash
cd Frontend
npm install
cp .env.example .env
# Set VITE_API_BASE_URL=http://localhost:3000
npm run dev
# Open: http://localhost:5173
```

---

## Docker Setup

### Quick start (backend + database)

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build

# API available at: http://localhost:3000
# Docs at: http://localhost:3000/docs
```

### With your models and outputs pre-loaded

```bash
# If you already ran the pipeline locally, models/ and outputs/ are mounted
docker compose up -d

# Check status
docker compose logs -f backend
docker compose ps

# Stop
docker compose down
```

### Frontend build for Docker

```bash
cd Frontend
npm run build
# Serve dist/ with any static file server or Nginx
```

---

## Deployment Guide

### Backend → Render

1. Create account at [render.com](https://render.com)
2. New → Web Service → Connect GitHub repo
3. Build settings:
   - **Build command:** `pip install -r backend/requirements.txt`
   - **Start command:** `uvicorn src.main:app --host 0.0.0.0 --port 3000 --app-dir src`
   - **Root directory:** leave blank (Render uses repo root)
4. Environment variables (set in Render dashboard):

   ``` bash
   DATABASE_URL=postgresql+asyncpg://...  (use Render PostgreSQL add-on)
   API_KEY_ADMIN=your-strong-key
   API_KEY_READONLY=your-readonly-key
   LLM_MODE=rules
   PORT=3000
   ```

5. Add PostgreSQL: Render dashboard → New → PostgreSQL → attach to service
6. Copy the internal `DATABASE_URL` from the PostgreSQL service into your web service env vars

### Frontend → GitHub Pages

1. Add to GitHub repository secrets:

   ``` bash
   VITE_API_BASE_URL=https://your-backend.onrender.com
   VITE_API_KEY_READONLY=your-readonly-key
   VITE_API_KEY_ADMIN=your-admin-key
   ```

2. Push to `main` branch
3. GitHub Actions will build and deploy automatically to `gh-pages` branch
4. Enable GitHub Pages in repo Settings → Pages → Source: `gh-pages`

### Frontend → Vercel (alternative)

```bash
cd Frontend
npx vercel deploy
# Set environment variables in Vercel dashboard
```

---

## API Overview

| Method | Endpoint | Description | Auth |
| -------- | ---------- | ------------- | ------ |
| GET | `/health` | System status | any |
| POST | `/predict` | Single customer churn prediction | any |
| POST | `/predict/batch` | Batch predictions (up to 10K) | any |
| POST | `/explain` | XAI explanation for customer | any |
| GET | `/explain/global` | Population-level feature importance | any |
| POST | `/upload` | Upload CSV/Excel, trigger pipeline | admin |
| GET | `/segments` | Segment churn + degradation status | any |
| GET | `/drift` | PSI + KS + early warning report | any |
| GET | `/insights` | 8-section intelligence report | any |
| POST | `/insights/qa` | Natural language Q&A | any |
| GET | `/customers/risk` | High-risk customer list | any |
| GET | `/watchlist` | Critical tier watchlist + reasoning | any |
| GET | `/models` | Model leaderboard | any |
| GET | `/report/pdf` | Download executive PDF | any |
| GET | `/report/excel` | Download cohort Excel | any |
| POST | `/pipeline/run` | Trigger full pipeline | admin |
| GET | `/pipeline/status/{id}` | Check pipeline progress | any |
| GET | `/logs` | System logs | admin |

All endpoints require `X-API-Key` header.

---

## Challenges and Solutions

### Scale: 6M row dataset in Python

**Challenge:** Pandas struggles with 6M rows on commodity hardware.
**Solution:** Data generator uses 50K-row chunks. Feature engineering is vectorized (no row-by-row loops). Model training uses only the base 500K rows; snapshots are used only for drift and segmentation calculations.

### XAI reliability: single-method SHAP isn't enough

**Challenge:** SHAP values can be unstable for tree ensembles with correlated features.
**Solution:** Agreement-based system. A feature explanation is only labeled HIGH confidence when SHAP, LIME, and AIX360 all independently agree on direction and relative rank. This eliminates false-confidence explanations.

### Drift detection false alarms

**Challenge:** PSI alone generates false positives when sample sizes differ between periods.
**Solution:** Combined drift assessment: a feature is only flagged as confirmed_drift when PSI ≥ 0.10 AND KS-test p < 0.05. R and Octave cross-validate the Python implementations independently.

### Async FastAPI with blocking ML operations

**Challenge:** ML inference (SHAP, model.predict) is CPU-bound and blocks the async event loop.
**Solution:** All blocking calls wrapped in `asyncio.to_thread()`. Background tasks use a separate thread pool via FastAPI's BackgroundTasks.

---

## Key Innovations

1. **Agreement-based XAI confidence** — Moving from "what does SHAP say?" to "what do SHAP + LIME + AIX360 all agree on?" produces dramatically more reliable customer explanations.

2. **Temporal degradation detection** — Most churn systems show you a snapshot. This system tracks acceleration: which segments are consistently getting worse month-over-month, not just which are currently bad.

3. **Cross-tool drift validation** — Python (PSI+KS) → R (independent KS + Spearman) → Octave (PSI + KL divergence). Three independent implementations must agree before a retraining trigger fires.

4. **RL-optimized recommendations** — The Q-learning recommender learns from outcomes over time. Early recommendations are prior-driven (domain knowledge); later recommendations are experience-driven (what actually reduced churn).

5. **Dual-mode frontend** — Demo mode (instant, precomputed) and Live mode (real pipeline) share identical UX, so users build intuition on the demo before trusting their own data results.

---

## Future Improvements

- **Real-time streaming** — Replace batch snapshots with Kafka event streams for true real-time drift detection
- **Model retraining automation** — Auto-trigger Phase 1 retraining when drift consensus fires, with A/B comparison before promotion
- **Multi-tenant** — Isolate data per customer organization with PostgreSQL row-level security
- **SHAP interaction values** — Extend XAI to capture pairwise feature interactions natively
- **Causal inference** — Replace correlation-based causal analysis with DoWhy/EconML for true causal effect estimation
- **Custom LLM fine-tuning** — Fine-tune a smaller model on customer health domain language for faster, cheaper inference
- **Mobile app** — React Native companion app for CSM daily watchlist review

---

## License

MIT License — see `Licence` file for details.

---

*Built with Python 3.11 · FastAPI · React 18 · TypeScript · Docker*
*Phase 8 complete — system production-ready*
