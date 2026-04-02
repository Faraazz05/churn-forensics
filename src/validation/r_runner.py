"""
r_runner.py
===========
Customer Health Forensics System — Phase 3 + 4
Python bridge to R statistical analysis scripts.

Calls R scripts via subprocess, passes file paths,
collects JSON output, and integrates results into the pipeline.

R scripts called:
  r/segmentation_analysis.R  — ANOVA, Tukey HSD, regression
  r/drift_validation.R       — KS cross-validation, PSI cross-check, correlation
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

R_DIR = Path(__file__).resolve().parent.parent.parent / "r"


def _check_r_available() -> bool:
    """Check if Rscript is on PATH."""
    try:
        result = subprocess.run(
            ["Rscript", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


R_AVAILABLE = _check_r_available()
if not R_AVAILABLE:
    print("[R-Runner] WARNING: Rscript not found. "
          "R validation will be skipped.\n"
          "  Install R: https://cloud.r-project.org/")


def _run_r_script(
    script_path: Path,
    args:        list[str],
    timeout:     int = 120,
) -> tuple[bool, str, str]:
    """
    Run an R script with arguments.

    Returns:
        (success, stdout, stderr)
    """
    cmd = ["Rscript", str(script_path)] + [str(a) for a in args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"R script timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def _load_json_output(path: Path) -> Optional[dict]:
    """Load JSON output produced by an R script."""
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[R-Runner] Failed to parse R output JSON: {e}")
        return None


# ── Segmentation analysis ──────────────────────────────────────
def run_segmentation_analysis(
    segment_df:    pd.DataFrame,
    dimension:     str = "plan_type",
    work_dir:      Path = None,
) -> dict:
    """
    Run R segmentation statistical analysis.

    Args:
        segment_df: DataFrame with segment results (from SegmentationEngine).
        dimension:  Which segment dimension to analyse (e.g. "plan_type").
        work_dir:   Working directory for temp files.

    Returns:
        R analysis results dict (ANOVA, Tukey, regression, significance).
        Returns {"status": "r_unavailable"} if R not installed.
    """
    if not R_AVAILABLE:
        return {"status": "r_unavailable",
                "message": "Rscript not found — install R to enable"}

    work_dir = work_dir or Path(tempfile.mkdtemp())
    work_dir.mkdir(parents=True, exist_ok=True)

    input_csv   = work_dir / "segment_results.csv"
    output_json = work_dir / "r_segmentation_output.json"
    script_path = R_DIR / "segmentation_analysis.R"

    if not script_path.exists():
        return {"status": "script_missing",
                "message": f"R script not found: {script_path}"}

    # Write segment data
    segment_df.to_csv(input_csv, index=False)
    print(f"[R-Runner] Running segmentation_analysis.R for dimension={dimension}...")

    success, stdout, stderr = _run_r_script(
        script_path = script_path,
        args        = [str(input_csv), str(output_json), dimension],
    )

    if stdout:
        for line in stdout.splitlines():
            print(f"  {line}")

    if not success:
        print(f"[R-Runner] R script failed: {stderr[:300]}")
        return {"status": "r_failed", "stderr": stderr[:500]}

    result = _load_json_output(output_json)
    if result is None:
        return {"status": "no_output"}

    result["r_stdout"]  = stdout
    result["dimension"] = dimension
    print(f"[R-Runner] Segmentation analysis complete. "
          f"ANOVA p={result.get('anova', {}).get('p_value', 'N/A')}")
    return result


# ── Drift validation ───────────────────────────────────────────
def run_drift_validation(
    df_reference:  pd.DataFrame,
    df_current:    pd.DataFrame,
    psi_df:        pd.DataFrame = None,
    work_dir:      Path = None,
) -> dict:
    """
    Run R drift statistical validation.

    Args:
        df_reference: Reference period feature DataFrame.
        df_current:   Current period feature DataFrame.
        psi_df:       Python PSI results for cross-check (optional).
        work_dir:     Working directory for temp files.

    Returns:
        R validation results dict (KS cross-validation, PSI cross-check, trends).
    """
    if not R_AVAILABLE:
        return {"status": "r_unavailable",
                "message": "Rscript not found — install R to enable"}

    work_dir = work_dir or Path(tempfile.mkdtemp())
    work_dir.mkdir(parents=True, exist_ok=True)

    EXCLUDE = {"customer_id", "churned", "churn_probability_true",
               "snapshot_month", "plan_type", "region",
               "contract_type", "payment_method"}

    numeric_cols = [c for c in df_reference.select_dtypes(include=[np.number]).columns
                    if c not in EXCLUDE]

    ref_numeric = df_reference[numeric_cols].copy()
    cur_numeric = df_current[numeric_cols].copy()

    ref_csv     = work_dir / "ref_data.csv"
    cur_csv     = work_dir / "cur_data.csv"
    psi_csv     = work_dir / "psi_results.csv"
    output_json = work_dir / "r_drift_output.json"
    script_path = R_DIR / "drift_validation.R"

    if not script_path.exists():
        return {"status": "script_missing",
                "message": f"R script not found: {script_path}"}

    ref_numeric.to_csv(ref_csv, index=False)
    cur_numeric.to_csv(cur_csv, index=False)

    if psi_df is not None and not psi_df.empty:
        psi_df[["feature", "psi"]].to_csv(psi_csv, index=False)
    else:
        pd.DataFrame(columns=["feature", "psi"]).to_csv(psi_csv, index=False)

    print("[R-Runner] Running drift_validation.R...")

    success, stdout, stderr = _run_r_script(
        script_path = script_path,
        args        = [str(ref_csv), str(cur_csv), str(psi_csv), str(output_json)],
    )

    if stdout:
        for line in stdout.splitlines():
            print(f"  {line}")

    if not success:
        print(f"[R-Runner] drift_validation.R failed: {stderr[:300]}")
        return {"status": "r_failed", "stderr": stderr[:500]}

    result = _load_json_output(output_json)
    if result is None:
        return {"status": "no_output"}

    summ = result.get("summary", {})
    print(f"[R-Runner] Drift validation complete. "
          f"KS-significant={summ.get('n_ks_significant', '?')} features, "
          f"PSI-agreement={summ.get('n_psi_agreements', '?')}/"
          f"{summ.get('n_psi_checked', '?')}")
    return result


# ── Convenience: print R findings ─────────────────────────────
def print_r_segmentation_findings(r_results: dict) -> None:
    """Pretty-print R segmentation analysis results."""
    if r_results.get("status") in ("r_unavailable", "r_failed", "no_output"):
        print(f"  [R] {r_results.get('message', r_results.get('status'))}")
        return

    print(f"\n── R Segmentation Findings ({r_results.get('dimension', '—')}) ──")

    anova = r_results.get("anova", {})
    if anova:
        print(f"  ANOVA: F={anova.get('f_statistic', '?')}  "
              f"p={anova.get('p_value', '?')}  "
              f"significant={'YES' if anova.get('significant') else 'NO'}  "
              f"effect={anova.get('effect_size', '?')}")
        print(f"  → {anova.get('interpretation', '')}")

    tukey = r_results.get("tukey_hsd", {})
    if tukey:
        print(f"  Tukey HSD: {tukey.get('n_significant_pairs', 0)} significant pairs")

    deg = r_results.get("degradation_significance", {})
    if deg and "p_value" in deg:
        print(f"  Degradation test: p={deg.get('p_value', '?')}  "
              f"{'SIGNIFICANT' if deg.get('significant') else 'not significant'}")
        print(f"  → {deg.get('interpretation', '')}")


def print_r_drift_findings(r_results: dict) -> None:
    """Pretty-print R drift validation results."""
    if r_results.get("status") in ("r_unavailable", "r_failed", "no_output"):
        print(f"  [R] {r_results.get('message', r_results.get('status'))}")
        return

    summ = r_results.get("summary", {})
    print(f"\n── R Drift Validation Findings ──────────────────────")
    print(f"  Features tested:    {summ.get('n_features_tested', '?')}")
    print(f"  KS significant:     {summ.get('n_ks_significant', '?')}")
    print(f"  PSI agreement:      "
          f"{summ.get('n_psi_agreements', '?')}/{summ.get('n_psi_checked', '?')}")
    print(f"  Significant trends: {summ.get('n_significant_trends', '?')}")
    print(f"  Validation passed:  {'YES' if summ.get('r_validation_passed') else 'NO'}")
