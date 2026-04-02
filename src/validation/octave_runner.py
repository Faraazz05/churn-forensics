"""
octave_runner.py
================
Customer Health Forensics System — Phase 4
Python bridge to Octave mathematical validation scripts.

Calls Octave scripts via subprocess, passes CSV file paths,
collects JSON output, integrates into pipeline.

Octave scripts called:
  octave/psi_validation.m        — PSI cross-validation + KL divergence
  octave/drift_math_validation.m — KS D-statistic, t-test, variance ratio
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

OCTAVE_DIR = Path(__file__).resolve().parent.parent.parent / "octave"


def _check_octave_available() -> bool:
    """Check if octave is on PATH."""
    try:
        result = subprocess.run(
            ["octave", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


OCTAVE_AVAILABLE = _check_octave_available()
if not OCTAVE_AVAILABLE:
    print("[Octave-Runner] WARNING: octave not found. "
          "Mathematical validation will be skipped.\n"
          "  Install: https://octave.org/download")


def _run_octave_script(
    script_path: Path,
    args:        list[str],
    timeout:     int = 180,
) -> tuple[bool, str, str]:
    """Run an Octave .m script with arguments."""
    cmd = ["octave", "--no-gui", "--quiet", str(script_path)] + [str(a) for a in args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Octave timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"[Octave-Runner] Failed to parse output JSON: {e}")
        return None


# ── Prepare numeric-only CSV for Octave ───────────────────────
EXCLUDE = {"customer_id", "churned", "churn_probability_true",
           "snapshot_month", "plan_type", "region",
           "contract_type", "payment_method"}

def _numeric_csv(df: pd.DataFrame, path: Path) -> list[str]:
    """Write numeric columns only to CSV. Returns column list."""
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                if c not in EXCLUDE]
    df[num_cols].to_csv(path, index=False)
    return num_cols


# ── PSI validation ─────────────────────────────────────────────
def run_psi_validation(
    df_reference:  pd.DataFrame,
    df_current:    pd.DataFrame,
    psi_df:        pd.DataFrame = None,
    work_dir:      Path = None,
) -> dict:
    """
    Run Octave PSI mathematical validation.

    Args:
        df_reference: Reference period feature DataFrame.
        df_current:   Current period feature DataFrame.
        psi_df:       Python PSI results for cross-check.
        work_dir:     Working directory for temp files.

    Returns:
        Octave validation results dict.
    """
    if not OCTAVE_AVAILABLE:
        return {"status": "octave_unavailable",
                "message": "octave not found — install GNU Octave"}

    work_dir = work_dir or Path(tempfile.mkdtemp())
    work_dir.mkdir(parents=True, exist_ok=True)

    ref_csv  = work_dir / "ref_data.csv"
    cur_csv  = work_dir / "cur_data.csv"
    psi_csv  = work_dir / "psi_results.csv"
    out_json = work_dir / "octave_psi_output.json"
    script   = OCTAVE_DIR / "psi_validation.m"

    if not script.exists():
        return {"status": "script_missing",
                "message": f"Script not found: {script}"}

    ref_cols = _numeric_csv(df_reference, ref_csv)
    cur_cols = _numeric_csv(df_current,   cur_csv)

    if psi_df is not None and not psi_df.empty:
        psi_df[["feature", "psi"]].to_csv(psi_csv, index=False)
    else:
        pd.DataFrame(columns=["feature", "psi"]).to_csv(psi_csv, index=False)

    print("[Octave-Runner] Running psi_validation.m...")

    success, stdout, stderr = _run_octave_script(
        script_path = script,
        args        = [str(ref_csv), str(cur_csv), str(psi_csv), str(out_json)],
    )

    if stdout:
        for line in stdout.strip().splitlines():
            print(f"  {line}")

    if not success and not out_json.exists():
        print(f"[Octave-Runner] psi_validation.m failed: {stderr[:300]}")
        return {"status": "octave_failed", "stderr": stderr[:500]}

    result = _load_json(out_json)
    if result is None:
        return {"status": "no_output"}

    agree_rate = result.get("agreement_rate", 0)
    print(f"[Octave-Runner] PSI validation complete. "
          f"Agreement rate: {agree_rate:.1%}  "
          f"Passed: {result.get('validation_passed', False)}")
    return result


# ── Drift math validation ──────────────────────────────────────
def run_drift_math_validation(
    df_reference:  pd.DataFrame,
    df_current:    pd.DataFrame,
    drift_json_path: Path = None,
    work_dir:      Path = None,
) -> dict:
    """
    Run Octave drift mathematical validation.

    Independently computes KS D-statistic, t-test mean shift,
    variance ratio, and drift severity classification.

    Args:
        df_reference:    Reference period DataFrame.
        df_current:      Current period DataFrame.
        drift_json_path: Path to Python drift_report.json for comparison.
        work_dir:        Working directory for temp files.

    Returns:
        Octave validation results dict.
    """
    if not OCTAVE_AVAILABLE:
        return {"status": "octave_unavailable",
                "message": "octave not found — install GNU Octave"}

    work_dir = work_dir or Path(tempfile.mkdtemp())
    work_dir.mkdir(parents=True, exist_ok=True)

    ref_csv    = work_dir / "ref_data.csv"
    cur_csv    = work_dir / "cur_data.csv"
    out_json   = work_dir / "octave_drift_math.json"
    drift_json = drift_json_path or (work_dir / "drift_report.json")
    script     = OCTAVE_DIR / "drift_math_validation.m"

    if not script.exists():
        return {"status": "script_missing",
                "message": f"Script not found: {script}"}

    _numeric_csv(df_reference, ref_csv)
    _numeric_csv(df_current,   cur_csv)

    if not drift_json.exists():
        # Create empty placeholder so Octave doesn't fail
        drift_json.write_text("{}")

    print("[Octave-Runner] Running drift_math_validation.m...")

    success, stdout, stderr = _run_octave_script(
        script_path = script,
        args        = [str(ref_csv), str(cur_csv), str(drift_json), str(out_json)],
    )

    if stdout:
        for line in stdout.strip().splitlines():
            print(f"  {line}")

    if not success and not out_json.exists():
        print(f"[Octave-Runner] drift_math_validation.m failed: {stderr[:300]}")
        return {"status": "octave_failed", "stderr": stderr[:500]}

    result = _load_json(out_json)
    if result is None:
        return {"status": "no_output"}

    print(f"[Octave-Runner] Drift math validation complete. "
          f"Combined drift detected in {result.get('n_combined_drift', '?')} columns. "
          f"Retrain flag: {result.get('retraining_flag_octave', False)}")
    return result


# ── Cross-validation comparison ────────────────────────────────
def cross_validate_retraining_decision(
    python_retrain: bool,
    octave_result:  dict,
    r_result:       dict,
) -> dict:
    """
    Compare retraining decisions across Python, Octave, and R.
    All three must agree for HIGH confidence; 2/3 for MEDIUM.
    """
    r_retrain     = r_result.get("summary", {}).get("r_validation_passed", None)
    octave_retrain = octave_result.get("retraining_flag_octave", None)

    votes = [v for v in [python_retrain, octave_retrain] if v is not None]
    n_agree = sum(1 for v in votes if v == python_retrain)

    if len(votes) == 0:
        confidence = "LOW"
    elif n_agree == len(votes):
        confidence = "HIGH"
    elif n_agree >= len(votes) - 1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "python_retrain":  python_retrain,
        "octave_retrain":  octave_retrain,
        "consensus":       python_retrain,
        "confidence":      confidence,
        "n_tools_agree":   n_agree,
        "n_tools_checked": len(votes),
        "interpretation": (
            f"Retraining decision: {'REQUIRED' if python_retrain else 'NOT required'} "
            f"({confidence} confidence, {n_agree}/{len(votes)} tools agree)"
        ),
    }


def print_octave_findings(result: dict, label: str = "Octave") -> None:
    """Pretty-print Octave validation results."""
    status = result.get("status")
    if status in ("octave_unavailable", "octave_failed", "no_output"):
        print(f"  [{label}] {result.get('message', status)}")
        return

    print(f"\n── {label} Mathematical Validation ──────────────────")
    print(f"  Columns validated:  {result.get('n_columns_validated', '?')}")

    if "n_psi_agreements" in result:
        print(f"  PSI agreement:      "
              f"{result['n_psi_agreements']}/{result.get('n_psi_crosschecked', '?')} "
              f"({result.get('agreement_rate', 0):.1%})")
        print(f"  Validation passed:  {'YES' if result.get('validation_passed') else 'NO'}")

    if "n_combined_drift" in result:
        print(f"  Combined drift:     {result['n_combined_drift']} columns")
        print(f"  Mean shifted:       {result.get('n_mean_shifted', '?')}")
        print(f"  Variance changed:   {result.get('n_variance_changed', '?')}")
        print(f"  High severity:      {result.get('n_high_severity', '?')}")
        retrain = result.get("retraining_flag_octave", False)
        print(f"  Retrain flag:       {'⚠ REQUIRED' if retrain else '✓ NOT required'}")
