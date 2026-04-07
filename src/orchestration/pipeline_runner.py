"""
pipeline_runner.py
==================
Customer Health Forensics System — Phase 3 + 4
Full multi-tool pipeline orchestrator.

Execution order (mandatory):
  1. Python — Segmentation Engine
  2. SQL    — Store results + run analytical queries
  3. R      — Statistical validation (ANOVA, Tukey, regression)
  4. Python — Drift Engine (PSI, KS-test, trend, early warning)
  5. Octave — Mathematical validation (PSI cross-check, KS-D, t-test)

Outputs combined intelligence report + per-layer artifacts.
"""

import json
import sys
import time
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# ── Path setup ──────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent.parent.parent
SRC  = HERE / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

from segmentation_engine import build_from_snapshots, SegmentationEngine
from cohort_analysis     import build_all_cohort_tables, build_trend_cohort, export_to_excel

# Import drift modules (same location as before — from existing phase34 src)
DRIFT_SRC = HERE.parent / "phase34" / "src"
if DRIFT_SRC.exists():
    sys.path.insert(0, str(DRIFT_SRC))
try:
    from drift_engine import DriftEngine
    from psi          import compute_psi_all_features
    from ks_test      import compute_ks_all_features
    DRIFT_AVAILABLE = True
except ImportError:
    DRIFT_AVAILABLE = False
    print("[Pipeline] WARNING: drift_engine not found. Copy psi.py, ks_test.py, drift_engine.py to src/")

from db.db_connector         import DBConnector
from validation.r_runner     import run_segmentation_analysis, run_drift_validation, \
                                    print_r_segmentation_findings, print_r_drift_findings
from validation.octave_runner import run_psi_validation, run_drift_math_validation, \
                                     cross_validate_retraining_decision, print_octave_findings


class NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.ndarray):    return o.tolist()
        return super().default(o)


def _save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, cls=NumpyEncoder)


def _banner(title: str):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print(f"{'='*62}")


def run_full_pipeline(
    data_dir:         Path,
    output_dir:       Path,
    xai_dir:          Path = None,
    db_config:        dict = None,
    current_month:    int  = None,
    previous_month:   int  = None,
    sample_size:      int  = None,
    skip_r:           bool = False,
    skip_octave:      bool = False,
    skip_db:          bool = False,
) -> dict:
    """
    Execute the full Phase 3 + 4 multi-tool pipeline.

    Layer order: Python → SQL → R → Python (Drift) → Octave

    Args:
        data_dir:      Path containing customers.csv + customers_snapshots.csv
        output_dir:    Root output directory
        xai_dir:       Phase 2 XAI outputs (for leading indicator cross-reference)
        db_config:     PostgreSQL config dict (host/port/dbname/user/password)
        current_month: Snapshot month to use as current (default: latest)
        previous_month: Snapshot month to use as reference (default: current-1)
        sample_size:   Limit rows loaded (for smoke testing)
        skip_r:        Skip R layer (for environments without R)
        skip_octave:   Skip Octave layer (for environments without Octave)
        skip_db:       Skip SQL layer (for environments without PostgreSQL)

    Returns:
        Combined intelligence dict.
    """
    t_total = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "_work"
    work_dir.mkdir(exist_ok=True)

    # ── Load snapshots ─────────────────────────────────────────
    snap_path = data_dir / "customers_snapshots.csv"
    base_path = data_dir / "customers.csv"

    if snap_path.exists():
        _banner("Loading 12-month snapshot data")
        df_snap = pd.read_csv(snap_path, nrows=sample_size)
        months  = sorted(df_snap["snapshot_month"].unique())
        print(f"  {len(df_snap):,} rows | months: {months}")

        # Validate it has multiple months — regenerate if it's single-month
        if len(months) <= 1 and base_path.exists():
            print(f"  [WARNING] Snapshot file only has {len(months)} month(s)")
            print(f"  Regenerating with 12-month drift simulation...")
            from data_generator import generate_snapshot_dataset
            generate_snapshot_dataset(snap_path, base_path, verbose=True)
            df_snap = pd.read_csv(snap_path, nrows=sample_size)
            months  = sorted(df_snap["snapshot_month"].unique())
            print(f"  Reloaded: {len(df_snap):,} rows | months: {months}")
    elif base_path.exists():
        print("[Pipeline] No snapshots found — generating 12-month snapshots from base data...")
        from data_generator import generate_snapshot_dataset
        generate_snapshot_dataset(snap_path, base_path, verbose=True)
        df_snap = pd.read_csv(snap_path, nrows=sample_size)
        months  = sorted(df_snap["snapshot_month"].unique())
        print(f"  Generated: {len(df_snap):,} rows | months: {months}")
    else:
        raise FileNotFoundError(f"No data found in {data_dir}. Run train.py first.")

    cur_m  = current_month  or months[-1]
    prev_m = previous_month or (cur_m - 1)
    df_cur  = df_snap[df_snap["snapshot_month"] == cur_m].copy()
    df_prev = df_snap[df_snap["snapshot_month"] == prev_m].copy() \
              if prev_m in months else None

    print(f"  Current month: {cur_m} ({len(df_cur):,} rows)")
    print(f"  Previous month: {prev_m} ({len(df_prev):,} rows if available)")

    # ── XAI top features (Phase 2 integration) ─────────────────
    xai_top_features = []
    if xai_dir and (xai_dir / "global_explanation.json").exists():
        with open(xai_dir / "global_explanation.json") as f:
            xai_data = json.load(f)
        xai_top_features = [x["feature"] for x in xai_data.get("top_features", [])[:10]]
        print(f"  XAI top features loaded: {xai_top_features[:4]}...")

    # ══════════════════════════════════════════════════════════
    # LAYER 1: Python — Segmentation Engine
    # ══════════════════════════════════════════════════════════
    _banner("LAYER 1 — Python: Segmentation Engine")
    engine      = build_from_snapshots(df_snap, current_month=cur_m, previous_month=prev_m)
    seg_results = engine.run()
    segments    = seg_results["segments"]
    insights    = seg_results["global_insights"]

    seg_dir = output_dir / "segmentation"
    seg_dir.mkdir(exist_ok=True)
    _save_json(segments, seg_dir / "segment_results.json")
    _save_json(insights,  seg_dir / "global_insights.json")

    # Cohort tables
    tables = build_all_cohort_tables(df_cur)
    cohort_dir = seg_dir / "cohort_tables"
    cohort_dir.mkdir(exist_ok=True)
    for name, tbl in tables.items():
        tbl.to_csv(cohort_dir / f"{name}.csv")

    # Trend cohorts
    for dim in engine.dimensions[:3]:
        trend = build_trend_cohort(df_snap, dim)
        if not trend.empty:
            trend.to_csv(seg_dir / f"trend_{dim}.csv")

    # Excel
    export_to_excel(tables, segments, seg_dir / "cohort_report.xlsx")

    # Save segment CSV for R + SQL
    seg_df = pd.DataFrame(segments)
    seg_csv = work_dir / "segment_results.csv"
    seg_df.to_csv(seg_csv, index=False)

    print(f"\n  Segments analyzed: {seg_results['n_segments_analyzed']}")
    print(f"  Degrading: {insights['n_degrading']} | "
          f"Improving: {insights['n_improving']} | "
          f"Accelerating: {insights['n_accelerating']}")

    # ══════════════════════════════════════════════════════════
    # LAYER 2: SQL — Store + Query
    # ══════════════════════════════════════════════════════════
    _banner("LAYER 2 — SQL: PostgreSQL Storage + Queries")
    db      = DBConnector(**(db_config or {}))
    run_id  = None
    sql_insights = {}

    if skip_db:
        print("  [SQL] Skipped (--skip-db)")
    elif not db.available:
        print("  [SQL] psycopg2/SQLAlchemy not installed — skipping DB layer")
    elif not db.test_connection():
        print("  [SQL] Database not reachable — skipping DB layer")
        print("        Set DB_HOST/DB_NAME/DB_USER/DB_PASSWORD env vars")
    else:
        db.init_schema()
        run_id = db.insert_pipeline_run(
            reference_month = prev_m,
            current_month   = cur_m,
            n_segments      = len(segments),
            overall_drift   = "PENDING",
            retrain_flag    = False,
            runtime_seconds = 0,
        )
        db.insert_segment_results(run_id, segments, snapshot_month=cur_m)
        sql_insights = db.query_all_insights(run_id)
        sql_dir = output_dir / "sql_outputs"
        sql_dir.mkdir(exist_ok=True)
        for name, df in sql_insights.items():
            df.to_csv(sql_dir / f"{name}.csv", index=False)
        print(f"  [SQL] Run ID: {run_id}")
        print(f"  [SQL] Queries run: {len(sql_insights)}")

    # ══════════════════════════════════════════════════════════
    # LAYER 3: R — Statistical Validation
    # ══════════════════════════════════════════════════════════
    _banner("LAYER 3 — R: Statistical Validation")
    r_results = {}

    if skip_r:
        print("  [R] Skipped (--skip-r)")
        r_results = {"status": "skipped"}
    else:
        # Run for primary dimension
        primary_dim = engine.dimensions[0] if engine.dimensions else "plan_type"
        r_seg = run_segmentation_analysis(
            segment_df = seg_df,
            dimension  = primary_dim,
            work_dir   = work_dir / "r_work",
        )
        print_r_segmentation_findings(r_seg)
        r_results["segmentation"] = r_seg

        r_seg_dir = output_dir / "r_outputs"
        r_seg_dir.mkdir(exist_ok=True)
        _save_json(r_seg, r_seg_dir / f"segmentation_{primary_dim}.json")

    # ══════════════════════════════════════════════════════════
    # LAYER 4: Python — Drift Engine
    # ══════════════════════════════════════════════════════════
    _banner("LAYER 4 — Python: Drift Detection Engine")
    drift_results = {}
    drift_dir     = output_dir / "drift"
    drift_dir.mkdir(exist_ok=True)

    if not DRIFT_AVAILABLE:
        print("  [Drift] drift_engine.py not found — place psi.py, ks_test.py, "
              "drift_engine.py in src/")
        drift_results = {"status": "drift_engine_missing"}
    else:
        drift_engine = DriftEngine(
            df_snapshots     = df_snap,
            reference_month  = prev_m if prev_m in months else months[0],
            current_month    = cur_m,
            xai_top_features = xai_top_features,
            verbose          = True,
        )
        drift_report = drift_engine.run()
        _save_json(drift_report, drift_dir / "drift_report.json")
        _save_json(drift_report.get("early_warnings", []),   drift_dir / "early_warnings.json")
        _save_json(drift_report.get("retraining_trigger",{}), drift_dir / "retraining_trigger.json")

        # Save PSI CSV for R + Octave cross-validation
        if drift_report.get("drift_report"):
            psi_df = pd.DataFrame(drift_report["drift_report"])[["feature","psi","psi_status"]]
            psi_df.to_csv(work_dir / "psi_results.csv", index=False)
            psi_df.to_csv(drift_dir / "psi_results.csv", index=False)

            ks_df = pd.DataFrame(drift_report["drift_report"])[
                ["feature","ks_statistic","p_value","ks_significant"]
            ]
            ks_df.to_csv(drift_dir / "ks_results.csv", index=False)

        drift_results = drift_report

        print(f"  Drift severity: {drift_report.get('overall_drift_severity')}")
        print(f"  Early warnings: {len(drift_report.get('early_warnings',[]))}")
        retrain = drift_report.get("retraining_trigger",{})
        print(f"  Retrain: {'⚠ REQUIRED' if retrain.get('model_retraining_required') else '✓ Not needed'}")

        # Run R drift validation
        if not skip_r:
            r_drift = run_drift_validation(
                df_reference = df_prev if df_prev is not None else df_cur,
                df_current   = df_cur,
                psi_df       = psi_df if "psi_df" in dir() else None,
                work_dir     = work_dir / "r_drift_work",
            )
            print_r_drift_findings(r_drift)
            _save_json(r_drift, output_dir / "r_outputs" / "drift_validation.json")
            r_results["drift"] = r_drift

        # Update SQL with drift results
        if run_id and db.available and not skip_db:
            db.insert_drift_results(
                run_id       = run_id,
                drift_report = drift_report.get("drift_report", []),
                warnings     = drift_report.get("early_warnings", []),
            )

    # ══════════════════════════════════════════════════════════
    # LAYER 5: Octave — Mathematical Validation
    # ══════════════════════════════════════════════════════════
    _banner("LAYER 5 — Octave: Mathematical Validation")
    octave_psi  = {}
    octave_drift = {}
    retrain_consensus = {}

    if skip_octave:
        print("  [Octave] Skipped (--skip-octave)")
    else:
        psi_csv_path = work_dir / "psi_results.csv"
        psi_df_for_oct = pd.read_csv(psi_csv_path) if psi_csv_path.exists() else None

        octave_psi = run_psi_validation(
            df_reference = df_prev if df_prev is not None else df_cur,
            df_current   = df_cur,
            psi_df       = psi_df_for_oct,
            work_dir     = work_dir / "octave_psi_work",
        )
        print_octave_findings(octave_psi, label="Octave PSI")
        _save_json(octave_psi, output_dir / "octave_outputs" / "psi_validation.json")

        octave_drift = run_drift_math_validation(
            df_reference     = df_prev if df_prev is not None else df_cur,
            df_current       = df_cur,
            drift_json_path  = drift_dir / "drift_report.json",
            work_dir         = work_dir / "octave_drift_work",
        )
        print_octave_findings(octave_drift, label="Octave Drift Math")
        _save_json(octave_drift, output_dir / "octave_outputs" / "drift_math_validation.json")

        # Cross-validate retraining decision
        py_retrain = drift_results.get("retraining_trigger",{}).get("model_retraining_required", False)
        retrain_consensus = cross_validate_retraining_decision(py_retrain, octave_drift, r_results.get("drift",{}))
        print(f"\n  {retrain_consensus['interpretation']}")
        _save_json(retrain_consensus, output_dir / "retrain_consensus.json")

    # ══════════════════════════════════════════════════════════
    # Combined intelligence report
    # ══════════════════════════════════════════════════════════
    _banner("COMBINED INTELLIGENCE REPORT")

    elapsed = round(time.time() - t_total, 1)

    intelligence = {
        "pipeline_version":    "Phase 3+4 Multi-Tool",
        "tools_used":          ["Python", "SQL", "R", "Octave"],
        "runtime_seconds":     elapsed,
        "current_month":       cur_m,
        "reference_month":     prev_m,
        "segmentation": {
            "n_segments":            seg_results["n_segments_analyzed"],
            "n_degrading":           insights["n_degrading"],
            "n_improving":           insights["n_improving"],
            "n_accelerating":        insights["n_accelerating"],
            "total_revenue_at_risk": insights["total_revenue_at_risk"],
            "top_degrading":         insights["top_degrading_segments"][:3],
        },
        "sql_layer": {
            "run_id":       run_id,
            "queries_run":  len(sql_insights),
            "available":    db.available and not skip_db,
        },
        "r_validation": {
            "segmentation_anova_p": (r_results.get("segmentation",{})
                                     .get("anova",{}).get("p_value")),
            "drift_psi_agreements": (r_results.get("drift",{})
                                     .get("summary",{}).get("n_psi_agreements")),
            "available":            not skip_r,
        },
        "drift": {
            "overall_severity":   drift_results.get("overall_drift_severity", "UNKNOWN"),
            "n_early_warnings":   len(drift_results.get("early_warnings", [])),
            "drifted_features":   drift_results.get("drifted_features", []),
            "retraining_required": drift_results.get("retraining_trigger",{})
                                                .get("model_retraining_required", False),
        },
        "octave_validation": {
            "psi_agreement_rate":     octave_psi.get("agreement_rate"),
            "psi_validation_passed":  octave_psi.get("validation_passed"),
            "retrain_consensus":      retrain_consensus,
            "available":              not skip_octave,
        },
        "output_dir": str(output_dir),
    }

    _save_json(intelligence, output_dir / "phase34_intelligence.json")

    print(f"  Runtime:            {elapsed}s")
    print(f"  Degrading segments: {insights['n_degrading']}")
    print(f"  Drift severity:     {drift_results.get('overall_drift_severity','—')}")
    print(f"  Retrain decision:   {retrain_consensus.get('interpretation','—')}")
    print(f"\n  Full report → {output_dir / 'phase34_intelligence.json'}")
    print(f"  Next → Phase 5: python run_insights.py")

    return intelligence
