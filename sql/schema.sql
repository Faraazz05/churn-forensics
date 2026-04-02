-- =============================================================
-- Customer Health Forensics System — Phase 3 + 4
-- PostgreSQL Schema
-- =============================================================
-- Run once to initialise the database before pipeline execution.
-- Compatible with PostgreSQL 14+
-- =============================================================

-- ── Extensions ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Drop tables (clean slate for reruns) ──────────────────────
DROP TABLE IF EXISTS drift_results       CASCADE;
DROP TABLE IF EXISTS early_warnings      CASCADE;
DROP TABLE IF EXISTS segment_snapshots   CASCADE;
DROP TABLE IF EXISTS segment_results     CASCADE;
DROP TABLE IF EXISTS pipeline_runs       CASCADE;

-- ── Pipeline run metadata ──────────────────────────────────────
CREATE TABLE pipeline_runs (
    run_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reference_month INT,
    current_month   INT,
    n_segments      INT,
    overall_drift   VARCHAR(10),
    retrain_flag    BOOLEAN DEFAULT FALSE,
    runtime_seconds NUMERIC(8,2),
    notes           TEXT
);

-- ── Segment results (Phase 3 output) ──────────────────────────
CREATE TABLE segment_results (
    id                  SERIAL PRIMARY KEY,
    run_id              UUID REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    segment_id          VARCHAR(100) NOT NULL,
    dimension           VARCHAR(50)  NOT NULL,
    value               VARCHAR(100) NOT NULL,
    snapshot_month      INT,

    -- Current metrics
    segment_size        INT,
    churn_rate          NUMERIC(6,4),
    avg_churn_prob      NUMERIC(6,4),
    n_churners          INT,
    avg_monthly_spend   NUMERIC(10,2),
    revenue_at_risk     NUMERIC(14,2),

    -- Temporal metrics
    previous_churn_rate NUMERIC(6,4),
    churn_delta         NUMERIC(6,4),
    velocity            VARCHAR(20),
    velocity_magnitude  VARCHAR(10),

    -- Classification
    health_status       VARCHAR(20),   -- improving / stable / degrading
    risk_level          VARCHAR(10),   -- low / medium / high
    acceleration        VARCHAR(30),   -- normal / accelerating_risk / decelerating

    -- Benchmark
    exceeds_benchmark   BOOLEAN DEFAULT FALSE,
    benchmark_note      TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── Segment snapshots (multi-period history) ───────────────────
CREATE TABLE segment_snapshots (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    segment_id      VARCHAR(100) NOT NULL,
    snapshot_month  INT NOT NULL,
    churn_rate      NUMERIC(6,4),
    segment_size    INT,
    revenue_at_risk NUMERIC(14,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Drift results (Phase 4 output) ────────────────────────────
CREATE TABLE drift_results (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    feature         VARCHAR(100) NOT NULL,
    psi             NUMERIC(8,6),
    psi_status      VARCHAR(25),   -- stable / monitor / significant_drift
    ks_statistic    NUMERIC(8,6),
    p_value         NUMERIC(10,8),
    ks_significant  BOOLEAN,
    confirmed_drift BOOLEAN DEFAULT FALSE,
    drift_severity  VARCHAR(10),   -- NONE / LOW / MEDIUM / HIGH
    trend           VARCHAR(20),   -- increasing / decreasing / stable
    velocity        VARCHAR(10),   -- low / medium / high
    slope           NUMERIC(10,6),
    pct_change      NUMERIC(8,4),
    impact          VARCHAR(100),
    early_warning   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Early warnings (Phase 4 output) ───────────────────────────
CREATE TABLE early_warnings (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    feature         VARCHAR(100) NOT NULL,
    psi             NUMERIC(8,6),
    trend           VARCHAR(20),
    velocity        VARCHAR(10),
    pct_change      NUMERIC(8,4),
    impact          VARCHAR(200),
    drift_severity  VARCHAR(10),
    xai_confirmed   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes for common query patterns ─────────────────────────
CREATE INDEX idx_seg_run        ON segment_results   (run_id);
CREATE INDEX idx_seg_dimension  ON segment_results   (dimension);
CREATE INDEX idx_seg_health     ON segment_results   (health_status);
CREATE INDEX idx_seg_risk       ON segment_results   (risk_level);
CREATE INDEX idx_seg_churn      ON segment_results   (churn_rate DESC);
CREATE INDEX idx_seg_delta      ON segment_results   (churn_delta DESC);
CREATE INDEX idx_snap_run       ON segment_snapshots (run_id, segment_id, snapshot_month);
CREATE INDEX idx_drift_run      ON drift_results     (run_id);
CREATE INDEX idx_drift_psi      ON drift_results     (psi DESC);
CREATE INDEX idx_drift_warning  ON drift_results     (early_warning);
CREATE INDEX idx_warn_run       ON early_warnings    (run_id);

-- ── Grant permissions (adjust role as needed) ─────────────────
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO churn_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO churn_user;

-- ── Useful view: degrading segments summary ────────────────────
CREATE OR REPLACE VIEW v_degrading_segments AS
SELECT
    sr.run_id,
    sr.segment_id,
    sr.dimension,
    sr.value,
    sr.churn_rate,
    sr.previous_churn_rate,
    sr.churn_delta,
    sr.revenue_at_risk,
    sr.risk_level,
    sr.acceleration,
    pr.run_timestamp
FROM segment_results sr
JOIN pipeline_runs   pr ON sr.run_id = pr.run_id
WHERE sr.health_status = 'degrading'
ORDER BY sr.churn_delta DESC;

-- ── Useful view: high-severity drift features ─────────────────
CREATE OR REPLACE VIEW v_drift_alerts AS
SELECT
    dr.run_id,
    dr.feature,
    dr.psi,
    dr.drift_severity,
    dr.trend,
    dr.velocity,
    dr.early_warning,
    dr.xai_confirmed,
    pr.run_timestamp
FROM drift_results  dr
JOIN pipeline_runs  pr ON dr.run_id = pr.run_id
WHERE dr.drift_severity IN ('HIGH', 'MEDIUM')
   OR dr.early_warning = TRUE
ORDER BY dr.psi DESC;

\echo 'Schema created successfully.'
