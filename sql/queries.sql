-- =============================================================
-- Customer Health Forensics System — Phase 3 + 4
-- SQL Analytical Queries
-- =============================================================
-- These queries are called programmatically by db_connector.py.
-- Each query is named (comment above) and parameterised
-- using %(param)s syntax (psycopg2 / SQLAlchemy compatible).
-- =============================================================


-- ── Q1: Top N Degrading Segments ─────────────────────────────
-- Returns segments with the largest positive churn_delta
-- (i.e. churn rate worsened the most since previous period).
-- Params: %(run_id)s, %(limit)s

-- name: top_degrading_segments
SELECT
    segment_id,
    dimension,
    value,
    churn_rate,
    previous_churn_rate,
    churn_delta,
    revenue_at_risk,
    risk_level,
    acceleration,
    exceeds_benchmark,
    benchmark_note
FROM segment_results
WHERE run_id = %(run_id)s
  AND health_status = 'degrading'
ORDER BY churn_delta DESC, revenue_at_risk DESC
LIMIT %(limit)s;


-- ── Q2: Top N Improving Segments ──────────────────────────────
-- Returns segments with the largest churn reduction.
-- Params: %(run_id)s, %(limit)s

-- name: top_improving_segments
SELECT
    segment_id,
    dimension,
    value,
    churn_rate,
    previous_churn_rate,
    churn_delta,
    revenue_at_risk
FROM segment_results
WHERE run_id = %(run_id)s
  AND health_status = 'improving'
ORDER BY churn_delta ASC
LIMIT %(limit)s;


-- ── Q3: Segment Churn Comparison by Dimension ─────────────────
-- Compare all segments within a single dimension.
-- Useful for plan_type, region, contract_type comparisons.
-- Params: %(run_id)s, %(dimension)s

-- name: segment_churn_by_dimension
SELECT
    value                           AS segment_value,
    segment_size,
    churn_rate,
    previous_churn_rate,
    churn_delta,
    revenue_at_risk,
    health_status,
    risk_level,
    exceeds_benchmark,
    ROUND(
        churn_rate - AVG(churn_rate) OVER (PARTITION BY dimension),
    4) AS vs_dimension_avg
FROM segment_results
WHERE run_id    = %(run_id)s
  AND dimension = %(dimension)s
ORDER BY churn_rate DESC;


-- ── Q4: Cohort Pivot — Plan × Region ──────────────────────────
-- Cross-tabulate churn rate by plan_type and region.
-- Params: %(run_id)s

-- name: cohort_plan_x_region
SELECT
    a.value                AS plan_type,
    b.value                AS region,
    ROUND(
        COALESCE(a.churn_rate, 0) * 0.5 +
        COALESCE(b.churn_rate, 0) * 0.5,
    4)                     AS blended_churn_rate,
    a.revenue_at_risk + COALESCE(b.revenue_at_risk, 0) AS combined_revenue_at_risk
FROM segment_results a
CROSS JOIN segment_results b
WHERE a.run_id    = %(run_id)s
  AND b.run_id    = %(run_id)s
  AND a.dimension = 'plan_type'
  AND b.dimension = 'region'
ORDER BY blended_churn_rate DESC;


-- ── Q5: Revenue at Risk Summary ───────────────────────────────
-- Total and per-dimension revenue at risk.
-- Params: %(run_id)s

-- name: revenue_at_risk_summary
SELECT
    dimension,
    COUNT(*)                       AS n_segments,
    ROUND(SUM(revenue_at_risk), 2) AS total_revenue_at_risk,
    ROUND(AVG(churn_rate),    4)   AS avg_churn_rate,
    SUM(CASE WHEN health_status = 'degrading' THEN 1 ELSE 0 END) AS n_degrading
FROM segment_results
WHERE run_id = %(run_id)s
GROUP BY dimension
ORDER BY total_revenue_at_risk DESC;


-- ── Q6: Accelerating Risk Segments ────────────────────────────
-- Segments where churn is consistently worsening across periods.
-- Params: %(run_id)s

-- name: accelerating_risk_segments
SELECT
    segment_id,
    dimension,
    value,
    churn_rate,
    churn_delta,
    velocity_magnitude,
    revenue_at_risk,
    exceeds_benchmark
FROM segment_results
WHERE run_id      = %(run_id)s
  AND acceleration = 'accelerating_risk'
ORDER BY churn_rate DESC, revenue_at_risk DESC;


-- ── Q7: Segments Exceeding SaaS Benchmark ─────────────────────
-- Segments with churn above industry median (7–10% monthly).
-- Params: %(run_id)s, %(benchmark_threshold)s (e.g. 0.08)

-- name: above_benchmark_segments
SELECT
    segment_id,
    dimension,
    value,
    churn_rate,
    churn_rate - %(benchmark_threshold)s AS above_benchmark_by,
    revenue_at_risk,
    health_status
FROM segment_results
WHERE run_id         = %(run_id)s
  AND exceeds_benchmark = TRUE
  AND churn_rate     > %(benchmark_threshold)s
ORDER BY churn_rate DESC;


-- ── Q8: Drift Features with Early Warning ─────────────────────
-- Features that are both drifting AND are leading indicators.
-- Params: %(run_id)s

-- name: early_warning_drift_features
SELECT
    feature,
    psi,
    psi_status,
    ks_statistic,
    p_value,
    drift_severity,
    trend,
    velocity,
    pct_change,
    impact,
    xai_confirmed
FROM drift_results
WHERE run_id       = %(run_id)s
  AND early_warning = TRUE
ORDER BY psi DESC;


-- ── Q9: Full Drift Summary ────────────────────────────────────
-- All features ranked by drift severity + PSI.
-- Params: %(run_id)s

-- name: full_drift_summary
SELECT
    feature,
    psi,
    psi_status,
    drift_severity,
    trend,
    velocity,
    early_warning,
    confirmed_drift,
    xai_confirmed
FROM drift_results
WHERE run_id = %(run_id)s
ORDER BY
    CASE drift_severity
        WHEN 'HIGH'   THEN 1
        WHEN 'MEDIUM' THEN 2
        WHEN 'LOW'    THEN 3
        ELSE               4
    END,
    psi DESC;


-- ── Q10: Month-over-Month Segment Trend ───────────────────────
-- Historical churn trend for a specific segment across months.
-- Params: %(segment_id)s

-- name: segment_trend_over_time
SELECT
    snapshot_month,
    churn_rate,
    segment_size,
    revenue_at_risk
FROM segment_snapshots
WHERE segment_id = %(segment_id)s
ORDER BY snapshot_month ASC;


-- ── Q11: Combined Intelligence View ───────────────────────────
-- Joins segment degradation + drift warnings for cross-reference.
-- Params: %(run_id)s

-- name: combined_intelligence
SELECT
    sr.segment_id,
    sr.dimension,
    sr.value,
    sr.churn_rate,
    sr.churn_delta,
    sr.health_status,
    sr.revenue_at_risk,
    sr.exceeds_benchmark,
    COUNT(ew.id)              AS n_early_warnings_active,
    MAX(dr.psi)               AS max_drift_psi,
    BOOL_OR(dr.early_warning) AS has_drift_warning
FROM segment_results  sr
LEFT JOIN early_warnings ew
    ON ew.run_id = sr.run_id
LEFT JOIN drift_results  dr
    ON dr.run_id = sr.run_id
    AND dr.early_warning = TRUE
WHERE sr.run_id = %(run_id)s
GROUP BY
    sr.segment_id, sr.dimension, sr.value,
    sr.churn_rate, sr.churn_delta, sr.health_status,
    sr.revenue_at_risk, sr.exceeds_benchmark
ORDER BY sr.churn_delta DESC NULLS LAST;


-- ── Q12: Latest Run Summary ────────────────────────────────────
-- Retrieve the most recent pipeline run metadata.
-- No params needed.

-- name: latest_run_summary
SELECT
    run_id,
    run_timestamp,
    reference_month,
    current_month,
    n_segments,
    overall_drift,
    retrain_flag,
    runtime_seconds
FROM pipeline_runs
ORDER BY run_timestamp DESC
LIMIT 1;
