"""
data_generator.py
=================
Customer Health Forensics System — Phase 1
Generates 500k synthetic customer records in memory-safe 50k chunks.
Also generates 12-month rolling snapshots (6M rows) for drift detection.

Churn label is structurally causal — derived from real business logic so
the ML model learns signal that SHAP/LIME/AIX360 can meaningfully explain.

Churn drivers baked into the data generation (in order of magnitude):
  1. last_login_days_ago  — inactivity is the #1 churn predictor
  2. logins_per_week      — engagement protects against churn
  3. support_tickets      — friction/dissatisfaction signal
  4. payment_failures     — financial stress indicator
  5. nps_score            — satisfaction acts as retention buffer
  6. contract_type        — monthly contracts churn ~2x annual
  7. plan_type            — enterprise is stickiest tier

Target churn rate: ~22% (realistic SaaS benchmark)
"""

import numpy as np
import pandas as pd
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────
RANDOM_SEED   = 42
TOTAL_RECORDS = 500_000
CHUNK_SIZE    = 50_000
N_MONTHS      = 12

# Intercept calibrated analytically:
# sigmoid(INTERCEPT + sum(coef * mean_feature_value)) = 0.22
# Derivation: logit(0.22) - sum(coef * mean) = 0.0358
# Verified: at mean feature values, churn probability = 0.220
CHURN_INTERCEPT = 0.036


# ── Internal helpers ───────────────────────────────────────────────────────
def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _generate_chunk(n: int, chunk_id: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate one chunk of n customer records.
    Pure function — no side effects, no I/O.
    All churn mechanics are deterministic given rng state.
    """

    # ── Customer profile ──────────────────────────────────────────────────
    age            = rng.integers(18, 70, n)
    tenure_months  = rng.integers(1, 72, n)
    plan_type      = rng.choice(["basic", "pro", "enterprise"], n, p=[0.45, 0.40, 0.15])
    contract_type  = rng.choice(["monthly", "annual"],          n, p=[0.60, 0.40])
    payment_method = rng.choice(["card", "paypal", "bank_transfer"], n, p=[0.55, 0.30, 0.15])
    region         = rng.choice(["North", "South", "East", "West", "Central"], n)

    # ── Engagement (plan-stratified realism) ──────────────────────────────
    eng_mult = np.where(plan_type == "enterprise", 1.4,
               np.where(plan_type == "pro",        1.0, 0.65))

    logins_per_week = np.clip(
        rng.normal(3.5, 2.0, n) * eng_mult, 0, 20
    ).round(1)

    features_used_count = np.clip(
        rng.normal(4.0, 2.5, n) * eng_mult, 1, 20
    ).astype(int)

    avg_session_duration_min = np.clip(
        rng.normal(18, 10, n), 1, 90
    ).round(1)

    monthly_active_days = np.clip(
        rng.normal(14, 7, n) * eng_mult, 0, 30
    ).round(0).astype(int)

    # Inactivity modelled as exponential — most users log in recently,
    # but a long tail of disengaged users exists
    last_login_days_ago = np.clip(
        rng.exponential(12, n), 0, 180
    ).round(0).astype(int)

    # ── Transaction data ──────────────────────────────────────────────────
    base_spend = np.where(plan_type == "enterprise", 299,
                 np.where(plan_type == "pro",        79, 29)).astype(float)
    monthly_spend = (base_spend * rng.uniform(0.8, 1.3, n)).round(2)

    payment_failures_last_6m = np.clip(rng.poisson(0.4, n), 0, 6)
    referrals_made            = np.clip(rng.poisson(0.8, n), 0, 10)

    # ── Support signals ───────────────────────────────────────────────────
    support_tickets_last_90d = np.clip(rng.poisson(1.2, n), 0, 15)
    nps_score = np.clip(rng.normal(6.5, 2.5, n), 0, 10).round(1)

    # ── Churn label: causal logistic model ───────────────────────────────
    # Coefficients mirror what a fitted Logistic Regression finds on real SaaS data.
    # This ensures XAI explanations recover meaningful, directionally-correct drivers.
    churn_logit = (
        CHURN_INTERCEPT
        + 0.045 * last_login_days_ago          # inactivity → risk+
        - 0.35  * logins_per_week              # engagement → risk-
        + 0.28  * support_tickets_last_90d     # friction   → risk+
        + 0.30  * payment_failures_last_6m     # stress     → risk+
        - 0.20  * nps_score                    # satisfaction → risk-
        + 0.18  * (contract_type == "monthly").astype(int)   # monthly → risk+
        - 0.15  * (plan_type == "enterprise").astype(int)    # enterprise → risk-
        + rng.normal(0, 0.25, n)               # residual noise
    )

    churn_prob = _sigmoid(churn_logit)
    churned    = (rng.uniform(0, 1, n) < churn_prob).astype(int)

    return pd.DataFrame({
        # Identifiers
        "customer_id": [f"CUST_{chunk_id * CHUNK_SIZE + i:07d}" for i in range(n)],
        # Profile
        "age":            age,
        "region":         region,
        "plan_type":      plan_type,
        "contract_type":  contract_type,
        "payment_method": payment_method,
        "tenure_months":  tenure_months,
        # Engagement
        "logins_per_week":           logins_per_week,
        "features_used_count":       features_used_count,
        "avg_session_duration_min":  avg_session_duration_min,
        "monthly_active_days":       monthly_active_days,
        "last_login_days_ago":       last_login_days_ago,
        # Transaction
        "monthly_spend":             monthly_spend,
        "payment_failures_last_6m":  payment_failures_last_6m,
        "referrals_made":            referrals_made,
        # Support
        "support_tickets_last_90d":  support_tickets_last_90d,
        "nps_score":                 nps_score,
        # Target
        "churned":                   churned,
        "churn_probability_true":    churn_prob.round(4),  # ground truth for validation
    })


# ── Public API ─────────────────────────────────────────────────────────────
def generate_main_dataset(
    output_path: Path,
    total_records: int = TOTAL_RECORDS,
    chunk_size:    int = CHUNK_SIZE,
    seed:          int = RANDOM_SEED,
    verbose:       bool = True,
) -> None:
    """
    Generate the full customer dataset in memory-safe chunks.
    Streams directly to CSV — never holds full dataset in RAM.

    Args:
        output_path:   Where to write customers.csv
        total_records: Number of synthetic customers (default 500k)
        chunk_size:    Rows per generation chunk (default 50k)
        seed:          Random seed for reproducibility
        verbose:       Print progress per chunk
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rng      = np.random.default_rng(seed)
    n_chunks = total_records // chunk_size
    first    = True

    if verbose:
        print(f"\n[DataGenerator] Generating {total_records:,} records "
              f"in {n_chunks} chunks of {chunk_size:,}...")

    for i in range(n_chunks):
        chunk = _generate_chunk(chunk_size, i, rng)
        chunk.to_csv(output_path, mode="w" if first else "a",
                     header=first, index=False)
        first = False

        if verbose:
            rate = chunk["churned"].mean()
            print(f"  Chunk {i+1:02d}/{n_chunks} | churn_rate={rate:.3f} | rows={len(chunk):,}")

    # Handle remainder rows if total_records not divisible by chunk_size
    remainder = total_records % chunk_size
    if remainder > 0:
        chunk = _generate_chunk(remainder, n_chunks, rng)
        chunk.to_csv(output_path, mode="a", header=False, index=False)
        if verbose:
            print(f"  Remainder chunk | rows={remainder:,}")

    size_mb = output_path.stat().st_size / 1e6
    if verbose:
        print(f"\n  Saved → {output_path}  ({size_mb:.1f} MB)")


def generate_snapshot_dataset(
    output_path: Path,
    base_path:   Path,
    n_months:    int  = N_MONTHS,
    seed:        int  = RANDOM_SEED + 100,
    verbose:     bool = True,
) -> None:
    """
    Generate 12-month rolling snapshots for drift detection.

    Months 1-7:  stable behaviour (reference period)
    Months 8-12: gradual engagement decay (drift period, 6% per month)
                 — this is the ground truth that PSI + KS-test should detect.

    Output: n_months * total_records rows  (12 * 500k = 6M rows)
    Memory-safe: loads base data once, modifies per month, streams to CSV.
    """
    output_path = Path(output_path)
    base_path   = Path(base_path)

    rng   = np.random.default_rng(seed)
    base  = pd.read_csv(base_path)
    first = True

    if verbose:
        print(f"\n[SnapshotGenerator] Generating {n_months}-month snapshots "
              f"({len(base) * n_months / 1e6:.1f}M rows)...")

    for month in range(1, n_months + 1):
        snap = base.copy()
        snap["snapshot_month"] = month

        if month >= 8:
            decay = 1.0 - (month - 7) * 0.06      # 6% decay per drift month
            noise = rng.normal(0, 0.04, len(snap))

            # Engagement decays
            snap["logins_per_week"] = np.clip(
                snap["logins_per_week"] * (decay + noise), 0, 20
            ).round(1)
            snap["monthly_active_days"] = np.clip(
                snap["monthly_active_days"] * (decay + noise * 0.5), 0, 30
            ).round(0).astype(int)

            # Payment stress increases slightly
            snap["payment_failures_last_6m"] = np.clip(
                snap["payment_failures_last_6m"] + rng.poisson(0.25, len(snap)), 0, 6
            )

        snap.to_csv(output_path, mode="w" if first else "a",
                    header=first, index=False)
        first = False

        if verbose:
            drift_tag = "DRIFT" if month >= 8 else "stable"
            print(f"  Month {month:02d} | churn={snap['churned'].mean():.3f} | {drift_tag}")

    size_mb = output_path.stat().st_size / 1e6
    if verbose:
        print(f"\n  Saved → {output_path}  ({size_mb:.1f} MB)")


def validate_dataset(df: pd.DataFrame, label: str = "") -> dict:
    """
    Run sanity checks on a sample of the generated data.
    Raises AssertionError if any check fails — designed to catch
    intercept miscalibration or broken generation logic early.
    """
    tag = f"[{label}] " if label else ""

    stats = {
        "n_rows":                len(df),
        "churn_rate":            round(float(df["churned"].mean()), 4),
        "plan_dist":             df["plan_type"].value_counts(normalize=True).round(3).to_dict(),
        "contract_dist":         df["contract_type"].value_counts(normalize=True).round(3).to_dict(),
        "avg_logins_per_week":   round(float(df["logins_per_week"].mean()), 2),
        "avg_last_login":        round(float(df["last_login_days_ago"].mean()), 1),
        "avg_nps":               round(float(df["nps_score"].mean()), 2),
        "missing_values":        int(df.isnull().sum().sum()),
        "customer_id_unique":    df["customer_id"].nunique() == len(df),
    }

    print(f"\n{tag}── Dataset Validation ──────────────────────")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    assert stats["missing_values"] == 0,           f"Missing values found"
    assert stats["customer_id_unique"],             f"Duplicate customer_ids"
    assert 0.15 <= stats["churn_rate"] <= 0.30,    \
        f"Churn rate {stats['churn_rate']:.3f} outside [0.15, 0.30] — check CHURN_INTERCEPT"
    assert stats["avg_last_login"] >= 5,            f"Avg last_login_days_ago suspiciously low"

    print(f"  ✓ All validation checks passed")
    return stats


if __name__ == "__main__":
    # Quick smoke-test: generate 10k rows locally to validate before Colab full run
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "customers_test.csv"
        generate_main_dataset(p, total_records=10_000, chunk_size=2_000, verbose=True)
        df = pd.read_csv(p)
        validate_dataset(df, label="10k smoke test")
        print("\n✓ data_generator.py smoke test passed")
