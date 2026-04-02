"""
run_full_pipeline.py
====================
Customer Health Forensics System — Phase 3 + 4
Single entry point for the full multi-tool pipeline.

Executes all 5 layers in sequence:
  1. Python — Segmentation Engine
  2. SQL    — PostgreSQL storage + analytical queries
  3. R      — Statistical validation (ANOVA, Tukey HSD, regression)
  4. Python — Drift Engine (PSI, KS-test, trend analysis, early warning)
  5. Octave — Mathematical validation (PSI cross-check, distribution math)

Usage:
  # Full run:
  python run_full_pipeline.py

  # Smoke test (fast, 5 months):
  python run_full_pipeline.py --sample 600000

  # Skip tools not installed:
  python run_full_pipeline.py --skip-db --skip-r --skip-octave

  # With PostgreSQL:
  python run_full_pipeline.py \\
      --db-host localhost --db-name customer_health \\
      --db-user postgres --db-password secret

  # With XAI Phase 2 integration:
  python run_full_pipeline.py --xai-dir outputs/xai

  # Custom paths (Colab):
  python run_full_pipeline.py \\
      --data-dir   /content/drive/MyDrive/CustomerHealth/data \\
      --output-dir /content/drive/MyDrive/CustomerHealth/outputs

  # Compare specific months:
  python run_full_pipeline.py --current-month 12 --previous-month 7

Outputs (outputs/):
  segmentation/
    segment_results.json      ← per-segment churn metrics
    global_insights.json      ← top degrading / improving / accelerating
    cohort_tables/            ← CSV pivot tables (plan×region, etc.)
    cohort_report.xlsx        ← formatted Excel workbook
    trend_*.csv               ← month-over-month trends
  sql_outputs/                ← CSV results of all SQL queries
  r_outputs/
    segmentation_*.json       ← ANOVA, Tukey HSD, regression results
    drift_validation.json     ← R KS cross-validation, PSI cross-check
  drift/
    drift_report.json         ← per-feature PSI + KS + trend + early_warning
    early_warnings.json       ← leading indicators in decline
    psi_results.csv           ← raw PSI scores
    ks_results.csv            ← raw KS-test results
    retraining_trigger.json   ← retraining decision
  octave_outputs/
    psi_validation.json       ← Octave PSI cross-check + KL divergence
    drift_math_validation.json ← KS-D, t-test, variance ratio
  retrain_consensus.json      ← cross-tool retraining decision
  phase34_intelligence.json   ← combined report → feeds Phase 5
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for candidate in [HERE / "src", HERE / "src" / "orchestration", HERE]:
    sys.path.insert(0, str(candidate))

from orchestration.pipeline_runner import run_full_pipeline

DEFAULT_DATA_DIR   = HERE / "data"
DEFAULT_OUTPUT_DIR = HERE / "outputs"


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3+4 Multi-Tool Pipeline — Customer Health Forensics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tool availability:
  SQL (PostgreSQL) — requires: pip install psycopg2-binary sqlalchemy
  R                — requires: R installed + jsonlite + dplyr packages
  Octave           — requires: GNU Octave installed

Quick start (Python only):
  python run_full_pipeline.py --skip-db --skip-r --skip-octave

Full run:
  python run_full_pipeline.py
        """,
    )
    # Paths
    parser.add_argument("--data-dir",       type=str, default=None)
    parser.add_argument("--output-dir",     type=str, default=None)
    parser.add_argument("--xai-dir",        type=str, default=None,
                        help="Path to Phase 2 XAI outputs (outputs/xai/)")
    # Months
    parser.add_argument("--current-month",  type=int, default=None)
    parser.add_argument("--previous-month", type=int, default=None)
    # Scale
    parser.add_argument("--sample",         type=int, default=None,
                        help="Limit snapshot rows (e.g. 600000 for 5 months)")
    # Database
    parser.add_argument("--skip-db",        action="store_true",
                        help="Skip PostgreSQL layer")
    parser.add_argument("--db-host",        type=str, default=None)
    parser.add_argument("--db-port",        type=int, default=5432)
    parser.add_argument("--db-name",        type=str, default="customer_health")
    parser.add_argument("--db-user",        type=str, default="postgres")
    parser.add_argument("--db-password",    type=str, default=None)
    # Tools
    parser.add_argument("--skip-r",         action="store_true",
                        help="Skip R statistical validation layer")
    parser.add_argument("--skip-octave",    action="store_true",
                        help="Skip Octave mathematical validation layer")

    args = parser.parse_args()

    db_config = None
    if not args.skip_db and args.db_host:
        db_config = {
            "host":     args.db_host,
            "port":     args.db_port,
            "dbname":   args.db_name,
            "user":     args.db_user,
            "password": args.db_password or "",
        }

    intelligence = run_full_pipeline(
        data_dir       = Path(args.data_dir)   if args.data_dir   else DEFAULT_DATA_DIR,
        output_dir     = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR,
        xai_dir        = Path(args.xai_dir)    if args.xai_dir    else None,
        db_config      = db_config,
        current_month  = args.current_month,
        previous_month = args.previous_month,
        sample_size    = args.sample,
        skip_r         = args.skip_r,
        skip_octave    = args.skip_octave,
        skip_db        = args.skip_db,
    )

    return intelligence


if __name__ == "__main__":
    main()
