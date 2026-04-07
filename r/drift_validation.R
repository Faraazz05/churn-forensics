# =============================================================
# Customer Health Forensics System — Phase 4
# R: Drift Statistical Validation
# =============================================================
# Called by r_runner.py via subprocess.
# Reads snapshot CSV, validates KS-test and PSI significance.
# Cross-validates Python drift engine outputs with R's own
# independent implementations.
#
# Arguments:
#   Rscript drift_validation.R <ref_csv> <cur_csv> <psi_csv> <output_json>
# =============================================================

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
})

# ── Arguments ──────────────────────────────────────────────────
args        <- commandArgs(trailingOnly = TRUE)
ref_csv     <- if (length(args) >= 1) args[1] else "ref_data.csv"
cur_csv     <- if (length(args) >= 2) args[2] else "cur_data.csv"
psi_csv     <- if (length(args) >= 3) args[3] else "psi_results.csv"
output_json <- if (length(args) >= 4) args[4] else "r_drift_output.json"

cat(sprintf("[R-Drift] Reference: %s\n", ref_csv))
cat(sprintf("[R-Drift] Current:   %s\n", cur_csv))

# ── Load data ──────────────────────────────────────────────────
df_ref <- tryCatch(read.csv(ref_csv, stringsAsFactors = FALSE),
                   error = function(e) stop(paste("[R] Cannot read ref CSV:", e$message)))
df_cur <- tryCatch(read.csv(cur_csv, stringsAsFactors = FALSE),
                   error = function(e) stop(paste("[R] Cannot read cur CSV:", e$message)))

cat(sprintf("[R-Drift] Ref rows: %d | Cur rows: %d\n", nrow(df_ref), nrow(df_cur)))

# Features to validate
EXCLUDE_COLS <- c("customer_id", "churned", "churn_probability_true",
                  "snapshot_month", "plan_type", "region",
                  "contract_type", "payment_method")

numeric_cols <- names(df_ref)[
  sapply(df_ref, is.numeric) &
  !names(df_ref) %in% EXCLUDE_COLS
]

cat(sprintf("[R-Drift] Validating %d features\n", length(numeric_cols)))

results <- list(
  status            = "success",
  n_features        = length(numeric_cols),
  ks_validations    = list(),
  psi_cross_check   = list(),
  trend_analysis    = list(),
  leading_indicators = list(),
  summary           = list()
)

# ── 1. Independent KS-test validation ─────────────────────────
cat("[R-Drift] Running KS-test validation...\n")

ks_results <- list()
for (col in numeric_cols) {
  if (!(col %in% names(df_cur))) next
  ref_vals <- df_ref[[col]][!is.na(df_ref[[col]])]
  cur_vals <- df_cur[[col]][!is.na(df_cur[[col]])]

  if (length(ref_vals) < 10 || length(cur_vals) < 10) next

  ks <- tryCatch(
    ks.test(ref_vals, cur_vals),
    error = function(e) NULL
  )
  if (is.null(ks)) next

  ks_results[[col]] <- list(
    feature      = col,
    ks_statistic = round(ks$statistic[[1]], 6),
    p_value      = round(ks$p.value, 8),
    significant  = ks$p.value < 0.05,
    r_conclusion = ifelse(ks$p.value < 0.05,
                          "Distribution shifted (R confirms)",
                          "Distribution stable (R confirms)")
  )
}

results$ks_validations <- ks_results
cat(sprintf("[R-Drift] KS-test validated for %d features\n", length(ks_results)))

# ── 2. PSI cross-check (R implementation) ─────────────────────
cat("[R-Drift] Cross-checking PSI with R implementation...\n")

compute_psi_r <- function(ref, cur, n_bins = 10) {
  eps        <- 1e-6
  breakpoints <- quantile(ref, probs = seq(0, 1, length.out = n_bins + 1),
                          na.rm = TRUE)
  breakpoints <- unique(breakpoints)
  if (length(breakpoints) < 2) return(NA_real_)

  # Extend breakpoints to cover current data range (prevents hist() error
  # when drift shifts values beyond reference distribution boundaries)
  full_range <- range(c(ref, cur), na.rm = TRUE)
  breakpoints[1]                  <- min(breakpoints[1], full_range[1]) - eps
  breakpoints[length(breakpoints)] <- max(breakpoints[length(breakpoints)], full_range[2]) + eps

  ref_counts <- hist(ref, breaks = breakpoints, plot = FALSE)$counts
  cur_counts <- hist(cur, breaks = breakpoints, plot = FALSE)$counts

  ref_pct <- ref_counts / (sum(ref_counts) + eps)
  cur_pct <- cur_counts / (sum(cur_counts) + eps)

  ref_pct[ref_pct == 0] <- eps
  cur_pct[cur_pct == 0] <- eps

  psi <- sum((cur_pct - ref_pct) * log(cur_pct / ref_pct))
  round(psi, 6)
}

# Load Python PSI results for cross-check
psi_cross <- list()
if (file.exists(psi_csv)) {
  py_psi <- tryCatch(read.csv(psi_csv, stringsAsFactors = FALSE),
                     error = function(e) NULL)

  if (!is.null(py_psi)) {
    for (i in seq_len(nrow(py_psi))) {
      col <- py_psi$feature[i]
      if (!(col %in% names(df_ref)) || !(col %in% names(df_cur))) next

      ref_vals <- df_ref[[col]][!is.na(df_ref[[col]])]
      cur_vals <- df_cur[[col]][!is.na(df_cur[[col]])]
      if (length(ref_vals) < 30 || length(cur_vals) < 30) next

      r_psi  <- compute_psi_r(ref_vals, cur_vals)
      py_psi_val <- py_psi$psi[i]
      delta  <- abs(r_psi - py_psi_val)

      psi_cross[[col]] <- list(
        feature    = col,
        python_psi = round(py_psi_val, 6),
        r_psi      = round(r_psi, 6),
        delta      = round(delta, 6),
        agreement  = delta < 0.01,
        status     = ifelse(delta < 0.01,
                            "AGREEMENT — R and Python PSI match",
                            "DISCREPANCY — investigate PSI implementation")
      )
    }
  }
}

results$psi_cross_check <- psi_cross
n_agree <- sum(sapply(psi_cross, function(x) isTRUE(x$agreement)))
cat(sprintf("[R-Drift] PSI cross-check: %d/%d features agree\n",
            n_agree, length(psi_cross)))

# ── 3. Trend regression validation ────────────────────────────
cat("[R-Drift] Running trend regression validation...\n")

# For each feature: linear regression of monthly mean against month number
if ("snapshot_month" %in% names(df_ref)) {
  df_both <- rbind(df_ref, df_cur)
  trend_results <- list()

  for (col in numeric_cols[1:min(10, length(numeric_cols))]) {
    if (!(col %in% names(df_both))) next
    monthly_means <- aggregate(df_both[[col]], by = list(df_both$snapshot_month), FUN = mean, na.rm = TRUE)
    names(monthly_means) <- c("month", "value")
    if (nrow(monthly_means) < 3) next

    reg <- tryCatch(
      lm(value ~ month, data = monthly_means),
      error = function(e) NULL
    )
    if (is.null(reg)) next

    summ <- summary(reg)
    slope   <- coef(reg)[["month"]]
    p_val   <- summ$coefficients["month", "Pr(>|t|)"]
    r_sq    <- summ$r.squared

    trend_results[[col]] <- list(
      feature         = col,
      slope           = round(slope, 6),
      r_squared       = round(r_sq, 4),
      p_value         = round(p_val, 6),
      significant     = p_val < 0.05,
      direction       = ifelse(slope > 0, "increasing", "decreasing"),
      r_interpretation = ifelse(
        p_val < 0.05,
        paste0("Significant ", ifelse(slope > 0, "upward", "downward"),
               " trend (slope=", round(slope, 4), ")"),
        "No statistically significant trend"
      )
    )
  }
  results$trend_analysis <- trend_results
}

# ── 4. Leading indicator correlation analysis ──────────────────
cat("[R-Drift] Correlating leading indicators with churn...\n")

leading_feats <- c("last_login_days_ago", "logins_per_week",
                   "engagement_score", "support_tickets_last_90d",
                   "payment_failures_last_6m", "monthly_active_days")

if ("churned" %in% names(df_ref)) {
  corr_results <- list()
  for (feat in leading_feats) {
    if (!(feat %in% names(df_ref))) next
    ref_vals  <- df_ref[[feat]]
    churn_vals <- df_ref$churned
    complete  <- complete.cases(ref_vals, churn_vals)
    if (sum(complete) < 30) next

    corr <- tryCatch(
      cor.test(ref_vals[complete], churn_vals[complete],
               method = "spearman"),
      error = function(e) NULL
    )
    if (is.null(corr)) next

    corr_results[[feat]] <- list(
      feature             = feat,
      spearman_rho        = round(corr$estimate[[1]], 4),
      p_value             = round(corr$p.value, 6),
      significant         = corr$p.value < 0.05,
      direction           = ifelse(corr$estimate[[1]] > 0, "positive", "negative"),
      churn_relationship  = ifelse(
        corr$p.value < 0.05,
        paste0("Significant ", ifelse(corr$estimate[[1]] > 0, "positive", "negative"),
               " correlation with churn (rho=", round(corr$estimate[[1]], 4), ")"),
        "No significant correlation with churn"
      )
    )
  }
  results$leading_indicators <- corr_results
}

# ── 5. Summary ─────────────────────────────────────────────────
n_sig_ks    <- sum(sapply(ks_results, function(x) isTRUE(x$significant)))
n_agree_psi <- n_agree
n_sig_trends <- if (length(results$trend_analysis) > 0)
  sum(sapply(results$trend_analysis, function(x) isTRUE(x$significant))) else 0

results$summary <- list(
  n_features_tested    = length(numeric_cols),
  n_ks_significant     = n_sig_ks,
  n_psi_agreements     = n_agree_psi,
  n_psi_checked        = length(psi_cross),
  n_significant_trends = n_sig_trends,
  r_validation_passed  = (n_agree_psi == length(psi_cross)) ||
                         (length(psi_cross) == 0)
)

cat(sprintf("[R-Drift] KS significant: %d | PSI agree: %d/%d | Trends: %d\n",
            n_sig_ks, n_agree, length(psi_cross), n_sig_trends))

# ── Write output ───────────────────────────────────────────────
write(toJSON(results, auto_unbox = TRUE, pretty = TRUE, na = "null"),
      output_json)

cat(sprintf("[R-Drift] Results written to: %s\n", output_json))
cat("[R-Drift] drift_validation.R complete.\n")
