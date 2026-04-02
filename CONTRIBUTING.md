# Contributing to Customer Health Forensics

Thank you for your interest in contributing. This document explains how to get started.

---

## Branching Strategy

```
main          ← production-ready, protected
develop       ← integration branch
feature/xyz   ← new features (branch from develop)
fix/xyz       ← bug fixes (branch from develop)
hotfix/xyz    ← critical production fixes (branch from main)
```

- All PRs target `develop`, not `main`.
- `main` is updated only via PR from `develop` after review.
- Branch names: `feature/phase8-docker`, `fix/xai-confidence-bug`

---

## Development Setup

```bash
# Clone
git clone https://github.com/your-org/customer_health_forensics.git
cd customer_health_forensics

# Python environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Backend
cp .env.example .env          # edit with your values
cd backend
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload --app-dir src

# Frontend
cd Frontend
npm install
cp .env.example .env          # edit VITE_API_BASE_URL
npm run dev
```

---

## Coding Standards

### Python (Phases 1–6)
- Style: follow PEP 8, enforced by `ruff`
- Type hints: required on all function signatures
- Docstrings: required on all classes and public functions
- Max line length: 100 characters
- Run before committing: `ruff check src/ backend/src/`

### TypeScript (Phase 7)
- Strict mode: enabled (`"strict": true` in tsconfig)
- No `any` types
- All component props must be typed with interfaces
- Functional components only, no class components
- Run before committing: `cd Frontend && npm run build`

---

## Pull Request Process

1. Create a branch from `develop`
2. Make your changes with clear, atomic commits
3. Ensure CI passes (lint + build)
4. Open PR with this template:
   - **What**: what does this PR do?
   - **Why**: what problem does it solve?
   - **Phase affected**: which phase(s) does it touch?
   - **Testing**: how was it tested?
5. Request review from at least one maintainer
6. Squash merge into `develop`

---

## Adding a New Phase or Feature

If extending the pipeline:
1. Add Python source to `src/`
2. Add a CLI runner at root level
3. Add a Colab notebook to `notebooks/`
4. Update `PROJECT_OVERVIEW.md` with inputs/outputs
5. Update backend services if the feature has an API endpoint
6. Update `README.md` with the new capability

---

## Commit Message Format

```
type(scope): short description

Types: feat | fix | docs | refactor | test | chore | ci
Scope: phase1 | phase2 | xai | drift | backend | frontend | docker

Examples:
  feat(drift): add Octave PSI cross-validation
  fix(backend): handle empty segment results in /segments
  docs(readme): add Docker deployment guide
  ci(actions): add Render deploy webhook step
```
