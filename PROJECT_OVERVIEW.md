# Project Overview — Customer Health Forensics System

Complete technical reference for all 8 phases.

---

## Phase 1 — Data Pipeline + ML Model Selection

**Goal:** Generate synthetic dataset, engineer features, select and train best model.

| | Detail |
|---|---|
| **Input** | None (generates synthetic data) |
| **Output** | `models/best_model.pkl`, `models/feature_names.json`, `models/leaderboard.csv`, `models/best_model_info.json` |
| **Dataset** | 500,000 customers × 12-month snapshots = 6M rows |
| **Features** | 12 engineered features: engagement_score, stickiness_index, spend_per_feature, support_to_usage_ratio, payment_risk_flag, recency_risk_flag, lifetime_value_est, nps_band, commitment_score, customer_health_score, engagement_rate, spend_per_active_day |
| **Models tested** | XGBoost, Logistic Regression (size-aware: tier selection based on dataset size) |
| **Selection rule** | If delta < 0.01 AUC → prefer XGBoost (SHAP TreeExplainer compatibility) |
| **Val AUC** | ~0.9273 |
| **Tools** | Python, scikit-learn, XGBoost, pandas, joblib |
| **Key files** | `src/data_generator.py`, `src/feature_engineering.py`, `src/model_selector.py`, `src/pipeline.py`, `train.py`, `test.py` |

---

## Phase 2 — Consensus XAI Engine

**Goal:** Explain predictions using agreement-based multi-method XAI. Confidence from agreement, not averaging.

| | Detail |
|---|---|
| **Input** | `models/best_model.pkl`, `models/feature_names.json`, customer data |
| **Output** | `outputs/xai/global_explanation.json`, `outputs/xai/watchlist_reasoning.json`, `outputs/xai/confidence_summary.json` |
| **XAI Methods** | SHAP (primary, TreeExplainer), LIME (validator), AIX360 (validator) |
| **Confidence rule** | HIGH = all 3 agree on direction + rank. MEDIUM = 2/3 agree. LOW = disagreement |
| **Watchlist** | Top 200 Critical-tier customers (prob ≥ 0.70), capped and sorted |
| **Tools** | Python, SHAP, LIME, AIX360 |
| **Key files** | `src/xai_engine.py`, `src/reasoning_layer.py`, `src/xai_runner.py`, `xai_run.py`, `xai_inspect.py` |

---

## Phase 3 — Segmentation Engine

**Goal:** Group customers into segments and detect temporal degradation.

| | Detail |
|---|---|
| **Input** | `data/customers_snapshots.csv`, Phase 1 features |
| **Output** | `outputs/segmentation/segment_results.json`, `outputs/segmentation/global_insights.json`, `outputs/segmentation/cohort_report.xlsx` |
| **Dimensions** | plan_type, region, contract_type, behavior_tier (engagement quartiles), nps_band_label |
| **Temporal metrics** | churn_rate, previous_churn_rate, churn_delta, velocity, acceleration |
| **Status classification** | degrading (delta > +0.10), improving (delta < -0.05), stable (otherwise) |
| **Acceleration** | accelerating_risk if consistently worsening across 3+ periods |
| **Benchmark** | SaaS industry median 8.5% monthly churn |
| **Tools** | Python, R (ANOVA + Tukey HSD + Wilcoxon), PostgreSQL (12 named queries), openpyxl |
| **Key files** | `src/segmentation_engine.py`, `src/cohort_analysis.py`, `sql/schema.sql`, `sql/queries.sql`, `r/segmentation_analysis.R`, `run_segmentation.py` |

---

## Phase 4 — Drift Detection + Early Warning

**Goal:** Detect feature distribution shifts and identify leading churn indicators before spikes.

| | Detail |
|---|---|
| **Input** | `data/customers_snapshots.csv` (multi-month), `outputs/xai/global_explanation.json` |
| **Output** | `outputs/drift/drift_report.json`, `outputs/drift/early_warnings.json`, `outputs/drift/retraining_trigger.json` |
| **PSI thresholds** | < 0.10 stable, 0.10–0.20 monitor, > 0.20 significant_drift |
| **KS-test** | p < 0.05 = significant, p < 0.01 = highly significant |
| **Confirmed drift** | PSI ≥ 0.10 AND KS p < 0.05 |
| **Leading indicators** | last_login_days_ago, logins_per_week, engagement_score, support_tickets_last_90d, payment_failures_last_6m, monthly_active_days |
| **Early warning** | feature is leading indicator AND trend is adverse AND PSI ≥ 0.10 |
| **Retraining trigger** | PSI > 0.20 on 3+ features simultaneously |
| **Tools** | Python, SciPy (KS-test), R (independent KS + Spearman correlation), Octave (PSI cross-validation + KL divergence) |
| **Key files** | `src/psi.py`, `src/ks_test.py`, `src/drift_engine.py`, `octave/psi_validation.m`, `octave/drift_math_validation.m`, `r/drift_validation.R`, `run_drift.py` |

---

## Phase 5 — Insight & Decision Intelligence Engine

**Goal:** Convert raw signals into executive-level intelligence, recommendations, and Q&A.

| | Detail |
|---|---|
| **Input** | All Phase 1–4 outputs |
| **Output** | `outputs/insights/intelligence_report.json` (8 sections), `outputs/insights/qa_log.json`, `outputs/insights/rl_policy.json` |
| **Rule engine** | 15 deterministic rules (R01–R15): engagement, payment, support, satisfaction, contract, adoption, health, tenure, stickiness |
| **ANN model** | sklearn MLPClassifier (64→32 hidden), feature impact scoring via perturbation, interaction detection |
| **RL recommender** | Q-learning with experience replay, 12 retention actions, ε-greedy, state = (risk_tier, driver_category) |
| **LLM** | LangChain + HuggingFace API (Mistral-7B), 7 Jinja2 templates, full rule-based fallback |
| **Q&A** | 16 intent patterns, context-aware answer generation |
| **Report sections** | Executive Summary, Customer Risk, Segment Intelligence, Drift & Behavior, Causal Analysis, Predictive Outlook, Recommendations, Business Impact |
| **Tools** | Python, sklearn, Jinja2, LangChain, HuggingFace |
| **Key files** | `src/rule_engine.py`, `src/ann_feature_model.py`, `src/rl_recommender.py`, `src/reasoning_engine.py`, `src/prompt_templates.py`, `src/llm_pipeline.py`, `src/insight_engine.py`, `src/qa_engine.py`, `insight_runner.py` |

---

## Phase 6 — FastAPI Backend

**Goal:** Expose all phase capabilities as a structured REST API.

| | Detail |
|---|---|
| **Input** | All phase outputs + real-time customer data via API calls |
| **Output** | JSON API responses, PDF/Excel reports on demand |
| **Port** | 3000 |
| **Auth** | API key (X-API-Key header), admin + read_only roles |
| **DB** | SQLite (dev), PostgreSQL (prod), async SQLAlchemy |
| **Tables** | uploads, customers, predictions, explanations, segment_results, drift_logs, insights, model_metadata, pipeline_runs |
| **Endpoints** | 20+ endpoints across: health, predict, explain, upload, segments, drift, insights, models, customers, reports, pipeline, admin |
| **Background tasks** | Upload → Phases 1–5 run asynchronously |
| **Tools** | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy async, aiosqlite/asyncpg |
| **Key files** | `src/main.py`, `src/core/`, `src/db/`, `src/services/`, `src/api/routes/`, `src/schemas/` |

---

## Phase 7 — React Frontend

**Goal:** Dual-mode customer intelligence platform — Demo (instant) and Live Analysis (real data).

| | Detail |
|---|---|
| **Input** | Backend API (all endpoints) |
| **Output** | Interactive web application |
| **Tech** | TypeScript, React 18, Vite, Tailwind CSS, Framer Motion, React Query, React Router v6, Recharts, Zustand |
| **Routes** | /, /demo, /demo/model, /demo/dashboard, /upload, /processing/:runId, /analysis/model, /analysis/dashboard, /customers/:id, /segments, /drift, /insights, /reports |
| **Entry paths** | "View Demo" → precomputed experience \| "Start Real Analysis" → upload + pipeline |
| **Key components** | AppShell (sidebar 240px + topbar 56px + RightPanel 420px), all chart components, all page components |
| **Key files** | `Frontend/src/main.tsx`, `Frontend/src/App.tsx`, `Frontend/src/types/api.ts`, `Frontend/src/api/client.ts`, all hooks |

---

## Phase 8 — Deployment & MLOps

**Goal:** Make the system production-ready, deployable, and maintainable.

| | Detail |
|---|---|
| **Docker** | `docker-compose.yml` (backend + postgres), `backend/Dockerfile` (non-root, healthcheck, 2 workers) |
| **CI/CD** | GitHub Actions: lint → test → Docker build → frontend build → Render deploy → GitHub Pages |
| **Backend hosting** | Render (free tier compatible, Docker-based) |
| **Frontend hosting** | GitHub Pages or Vercel |
| **MLOps** | Model versioning (`models/v1/`), retraining trigger from drift output, pipeline run tracking |
| **Monitoring** | Structured JSON logging, `/health` endpoint, request timing middleware |
| **Documentation** | README.md (full product doc), PROJECT_OVERVIEW.md, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md |

---

## Phase Dependencies

```
Phase 1 ──────────────────────────────────────────────────────┐
    └── Phase 2 (XAI) ────────────────────────────────────────┤
    └── Phase 3 (Segmentation) ──────────────────────────────┤
    └── Phase 4 (Drift) ─────────────────────────────────────┤
                                                               ▼
                            Phase 5 (Insights) ← uses all 1–4 outputs
                                    │
                                    ▼
                            Phase 6 (Backend API) ← serves all outputs
                                    │
                                    ▼
                            Phase 7 (Frontend) ← calls backend
                                    │
                                    ▼
                            Phase 8 (Deployment) ← orchestrates all
```
