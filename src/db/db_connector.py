"""
db_connector.py
===============
Customer Health Forensics System — Phase 3 + 4
PostgreSQL database connector.

Handles:
  - Connection management (SQLAlchemy + psycopg2)
  - Schema initialisation
  - Inserting Phase 3 segment results
  - Inserting Phase 4 drift results
  - Running all named analytical queries from queries.sql
  - Returning results as DataFrames

Configuration via environment variables or explicit kwargs:
  DB_HOST     (default: localhost)
  DB_PORT     (default: 5432)
  DB_NAME     (default: customer_health)
  DB_USER     (default: postgres)
  DB_PASSWORD (default: postgres)
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    import psycopg2
    import psycopg2.extras
    from sqlalchemy import create_engine, text
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"


# ── Connection config ──────────────────────────────────────────
def _get_config(**overrides) -> dict:
    return {
        "host":     overrides.get("host",     os.getenv("DB_HOST",     "localhost")),
        "port":     overrides.get("port",     int(os.getenv("DB_PORT", "5432"))),
        "dbname":   overrides.get("dbname",   os.getenv("DB_NAME",     "customer_health")),
        "user":     overrides.get("user",     os.getenv("DB_USER",     "postgres")),
        "password": overrides.get("password", os.getenv("DB_PASSWORD", "postgres")),
    }


def _conn_string(**overrides) -> str:
    c = _get_config(**overrides)
    return (f"postgresql+psycopg2://{c['user']}:{c['password']}"
            f"@{c['host']}:{c['port']}/{c['dbname']}")


# ── DBConnector class ──────────────────────────────────────────
class DBConnector:
    """
    PostgreSQL connector for Phase 3 + 4 pipeline.

    Usage:
        db = DBConnector()
        if db.available:
            db.init_schema()
            run_id = db.insert_pipeline_run(...)
            db.insert_segment_results(run_id, segments)
            df = db.query("top_degrading_segments", run_id=run_id, limit=5)
    """

    def __init__(self, **config_overrides):
        self.available  = DB_AVAILABLE
        self._config    = _get_config(**config_overrides)
        self._engine    = None
        self._queries   = self._load_named_queries()

        if not DB_AVAILABLE:
            print("[DB] psycopg2 / SQLAlchemy not installed — DB layer disabled.")
            print("     Run: pip install psycopg2-binary sqlalchemy")

    def _get_engine(self):
        if self._engine is None:
            conn_str     = _conn_string(**self._config)
            self._engine = create_engine(conn_str, pool_pre_ping=True)
        return self._engine

    def _load_named_queries(self) -> dict[str, str]:
        """
        Parse queries.sql and extract named queries.
        Each query is preceded by:  -- name: query_name
        """
        queries = {}
        sql_file = SQL_DIR / "queries.sql"
        if not sql_file.exists():
            return {}

        content    = sql_file.read_text()
        # Split on -- name: markers
        pattern    = r"--\s*name:\s*(\w+)\n(.*?)(?=--\s*name:|\Z)"
        matches    = re.findall(pattern, content, re.DOTALL)

        for name, body in matches:
            # Strip comment lines but keep SQL
            lines = [l for l in body.strip().splitlines()
                     if not l.strip().startswith("--")]
            queries[name.strip()] = "\n".join(lines).strip()

        return queries

    def test_connection(self) -> bool:
        """Return True if database is reachable."""
        if not self.available:
            return False
        try:
            with self._get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"[DB] Connection failed: {e}")
            return False

    def init_schema(self, schema_path: Path = None) -> bool:
        """Run schema.sql to create all tables."""
        if not self.available:
            return False
        schema_file = schema_path or (SQL_DIR / "schema.sql")
        if not schema_file.exists():
            print(f"[DB] Schema file not found: {schema_file}")
            return False
        try:
            sql = schema_file.read_text()
            # Split on semicolons, execute each statement
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            with self._get_engine().connect() as conn:
                for stmt in statements:
                    if stmt.upper().startswith(("CREATE", "DROP", "GRANT",
                                                "INSERT", "ALTER", "\\ECHO")):
                        try:
                            conn.execute(text(stmt))
                        except Exception:
                            pass   # skip unsupported statements like \echo
                conn.commit()
            print("[DB] Schema initialised successfully.")
            return True
        except Exception as e:
            print(f"[DB] Schema init failed: {e}")
            return False

    # ── Pipeline run ───────────────────────────────────────────
    def insert_pipeline_run(
        self,
        reference_month:  int,
        current_month:    int,
        n_segments:       int,
        overall_drift:    str,
        retrain_flag:     bool,
        runtime_seconds:  float,
        notes:            str = "",
    ) -> str:
        """Insert a pipeline run record. Returns run_id (UUID string)."""
        if not self.available:
            return str(uuid.uuid4())   # return dummy ID if DB unavailable

        run_id = str(uuid.uuid4())
        sql = """
            INSERT INTO pipeline_runs
            (run_id, reference_month, current_month, n_segments,
             overall_drift, retrain_flag, runtime_seconds, notes)
            VALUES
            (:run_id, :ref_month, :cur_month, :n_segments,
             :overall_drift, :retrain_flag, :runtime_seconds, :notes)
        """
        try:
            with self._get_engine().connect() as conn:
                conn.execute(text(sql), {
                    "run_id":          run_id,
                    "ref_month":       reference_month,
                    "cur_month":       current_month,
                    "n_segments":      n_segments,
                    "overall_drift":   overall_drift,
                    "retrain_flag":    retrain_flag,
                    "runtime_seconds": runtime_seconds,
                    "notes":           notes,
                })
                conn.commit()
            print(f"[DB] Pipeline run inserted: {run_id}")
        except Exception as e:
            print(f"[DB] insert_pipeline_run failed: {e}")
        return run_id

    # ── Segment results ────────────────────────────────────────
    def insert_segment_results(
        self,
        run_id:   str,
        segments: list[dict],
        snapshot_month: int = None,
    ) -> int:
        """Bulk insert segment results. Returns rows inserted."""
        if not self.available or not segments:
            return 0

        sql = """
            INSERT INTO segment_results
            (run_id, segment_id, dimension, value, snapshot_month,
             segment_size, churn_rate, avg_churn_prob, n_churners,
             avg_monthly_spend, revenue_at_risk,
             previous_churn_rate, churn_delta, velocity, velocity_magnitude,
             health_status, risk_level, acceleration,
             exceeds_benchmark, benchmark_note)
            VALUES
            (:run_id, :segment_id, :dimension, :value, :snapshot_month,
             :segment_size, :churn_rate, :avg_churn_prob, :n_churners,
             :avg_monthly_spend, :revenue_at_risk,
             :prev_churn_rate, :churn_delta, :velocity, :velocity_mag,
             :health_status, :risk_level, :acceleration,
             :exceeds_benchmark, :benchmark_note)
        """
        rows = []
        for s in segments:
            rows.append({
                "run_id":           run_id,
                "segment_id":       s.get("segment_id", ""),
                "dimension":        s.get("dimension", ""),
                "value":            str(s.get("value", "")),
                "snapshot_month":   snapshot_month,
                "segment_size":     s.get("segment_size"),
                "churn_rate":       s.get("churn_rate"),
                "avg_churn_prob":   s.get("avg_churn_probability"),
                "n_churners":       s.get("n_churners"),
                "avg_monthly_spend": s.get("avg_monthly_spend"),
                "revenue_at_risk":  s.get("revenue_at_risk"),
                "prev_churn_rate":  s.get("previous_churn_rate"),
                "churn_delta":      s.get("churn_delta"),
                "velocity":         s.get("velocity"),
                "velocity_mag":     s.get("velocity_magnitude"),
                "health_status":    s.get("health_status"),
                "risk_level":       s.get("risk_level"),
                "acceleration":     s.get("acceleration"),
                "exceeds_benchmark": s.get("exceeds_benchmark", False),
                "benchmark_note":   s.get("benchmark_note", ""),
            })

        try:
            with self._get_engine().connect() as conn:
                conn.execute(text(sql), rows)
                conn.commit()
            print(f"[DB] Inserted {len(rows)} segment results")
            return len(rows)
        except Exception as e:
            print(f"[DB] insert_segment_results failed: {e}")
            return 0

    # ── Drift results ──────────────────────────────────────────
    def insert_drift_results(
        self,
        run_id:       str,
        drift_report: list[dict],
        warnings:     list[dict],
    ) -> int:
        """Insert drift per-feature results and early warnings."""
        if not self.available:
            return 0

        drift_sql = """
            INSERT INTO drift_results
            (run_id, feature, psi, psi_status, ks_statistic, p_value,
             ks_significant, confirmed_drift, drift_severity,
             trend, velocity, slope, pct_change, impact, early_warning)
            VALUES
            (:run_id, :feature, :psi, :psi_status, :ks_statistic, :p_value,
             :ks_significant, :confirmed_drift, :drift_severity,
             :trend, :velocity, :slope, :pct_change, :impact, :early_warning)
        """
        warn_sql = """
            INSERT INTO early_warnings
            (run_id, feature, psi, trend, velocity, pct_change,
             impact, drift_severity, xai_confirmed)
            VALUES
            (:run_id, :feature, :psi, :trend, :velocity, :pct_change,
             :impact, :drift_severity, :xai_confirmed)
        """

        try:
            with self._get_engine().connect() as conn:
                drift_rows = [{
                    "run_id":         run_id,
                    "feature":        d.get("feature"),
                    "psi":            d.get("psi"),
                    "psi_status":     d.get("psi_status"),
                    "ks_statistic":   d.get("ks_statistic"),
                    "p_value":        d.get("p_value"),
                    "ks_significant": d.get("ks_significant"),
                    "confirmed_drift": d.get("confirmed_drift"),
                    "drift_severity": d.get("drift_severity"),
                    "trend":          d.get("trend"),
                    "velocity":       d.get("velocity"),
                    "slope":          d.get("slope"),
                    "pct_change":     d.get("pct_change"),
                    "impact":         d.get("impact"),
                    "early_warning":  d.get("early_warning"),
                } for d in drift_report]
                conn.execute(text(drift_sql), drift_rows)

                warn_rows = [{
                    "run_id":        run_id,
                    "feature":       w.get("feature"),
                    "psi":           w.get("psi"),
                    "trend":         w.get("trend"),
                    "velocity":      w.get("velocity"),
                    "pct_change":    w.get("pct_change"),
                    "impact":        w.get("impact"),
                    "drift_severity": w.get("drift_severity"),
                    "xai_confirmed": w.get("xai_confirmed", False),
                } for w in warnings]
                if warn_rows:
                    conn.execute(text(warn_sql), warn_rows)

                conn.commit()
            print(f"[DB] Inserted {len(drift_rows)} drift features, "
                  f"{len(warn_rows)} warnings")
            return len(drift_rows)
        except Exception as e:
            print(f"[DB] insert_drift_results failed: {e}")
            return 0

    # ── Query runner ───────────────────────────────────────────
    def query(self, query_name: str, **params) -> Optional[pd.DataFrame]:
        """
        Run a named query from queries.sql with the given params.

        Args:
            query_name: Key matching a -- name: tag in queries.sql
            **params:   Named parameters for the query

        Returns:
            DataFrame with results, or None if unavailable/failed.
        """
        if not self.available:
            print(f"[DB] Unavailable — cannot run query '{query_name}'")
            return None

        if query_name not in self._queries:
            print(f"[DB] Query not found: '{query_name}'")
            print(f"     Available: {list(self._queries.keys())}")
            return None

        sql_str = self._queries[query_name]
        try:
            with self._get_engine().connect() as conn:
                df = pd.read_sql(text(sql_str), conn, params=params)
            return df
        except Exception as e:
            print(f"[DB] Query '{query_name}' failed: {e}")
            return None

    def query_all_insights(self, run_id: str) -> dict[str, pd.DataFrame]:
        """Run all standard insight queries for a run. Returns dict of DataFrames."""
        results = {}

        queries_to_run = {
            "top_degrading":  ("top_degrading_segments",   {"run_id": run_id, "limit": 10}),
            "top_improving":  ("top_improving_segments",   {"run_id": run_id, "limit": 5}),
            "revenue_risk":   ("revenue_at_risk_summary",  {"run_id": run_id}),
            "accelerating":   ("accelerating_risk_segments", {"run_id": run_id}),
            "drift_features": ("full_drift_summary",       {"run_id": run_id}),
            "early_warnings": ("early_warning_drift_features", {"run_id": run_id}),
            "combined_intel": ("combined_intelligence",    {"run_id": run_id}),
        }

        for label, (qname, params) in queries_to_run.items():
            df = self.query(qname, **params)
            if df is not None:
                results[label] = df
                print(f"[DB] {label}: {len(df)} rows")

        return results

    def get_latest_run_id(self) -> Optional[str]:
        """Return the run_id of the most recent pipeline run."""
        df = self.query("latest_run_summary")
        if df is not None and len(df) > 0:
            return str(df.iloc[0]["run_id"])
        return None
