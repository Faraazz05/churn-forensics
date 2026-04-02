# =============================================================
# Customer Health Forensics System — Phase 3
# R: Segmentation Statistical Analysis
# =============================================================
# Called by r_runner.py via subprocess.
# Reads segment_results.csv, runs statistical tests,
# outputs results to r_segmentation_output.json.
#
# Analyses performed:
#   1. One-way ANOVA: are churn rates significantly different across segments?
#   2. Tukey HSD post-hoc: which pairs of segments differ significantly?
#   3. Linear regression: which segment features predict churn_rate?
#   4. Effect size (eta-squared): practical significance of differences
#
# Arguments (command line):
#   Rscript segmentation_analysis.R <input_csv> <output_json> <dimension>
# =============================================================

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
})

# ── Arguments ──────────────────────────────────────────────────
args       <- commandArgs(trailingOnly = TRUE)
input_csv  <- if (length(args) >= 1) args[1] else "segment_results.csv"
output_json <- if (length(args) >= 2) args[2] else "r_segmentation_output.json"
dimension  <- if (length(args) >= 3) args[3] else "plan_type"

cat(sprintf("[R] Loading: %s\n", input_csv))
cat(sprintf("[R] Dimension: %s\n", dimension))

# ── Load data ──────────────────────────────────────────────────
df <- tryCatch(
  read.csv(input_csv, stringsAsFactors = FALSE),
  error = function(e) stop(paste("[R] Cannot read input CSV:", e$message))
)

cat(sprintf("[R] Rows loaded: %d\n", nrow(df)))

# Filter to requested dimension
if ("dimension" %in% names(df)) {
  df_dim <- df[df$dimension == dimension, ]
} else {
  df_dim <- df
}

if (nrow(df_dim) < 2) {
  result <- list(
    status  = "insufficient_data",
    message = paste("Need >= 2 segments for dimension:", dimension),
    dimension = dimension
  )
  write(toJSON(result, auto_unbox = TRUE, pretty = TRUE), output_json)
  cat("[R] Insufficient data — skipping analysis.\n")
  quit(status = 0)
}

results <- list(
  dimension      = dimension,
  n_segments     = nrow(df_dim),
  status         = "success"
)

# ── 1. Descriptive statistics ──────────────────────────────────
cat("[R] Computing descriptive statistics...\n")

desc <- df_dim %>%
  group_by(value) %>%
  summarise(
    n             = n(),
    churn_rate    = round(mean(churn_rate, na.rm = TRUE), 4),
    churn_delta   = round(mean(churn_delta, na.rm = TRUE), 4),
    revenue_risk  = round(mean(revenue_at_risk, na.rm = TRUE), 2),
    .groups = "drop"
  )

results$descriptive_stats <- lapply(1:nrow(desc), function(i) {
  as.list(desc[i, ])
})

# ── 2. ANOVA: churn_rate ~ segment ────────────────────────────
cat("[R] Running one-way ANOVA...\n")

df_dim$segment_factor <- as.factor(df_dim$value)

anova_result <- tryCatch({
  aov_model   <- aov(churn_rate ~ segment_factor, data = df_dim)
  aov_summary <- summary(aov_model)[[1]]

  f_stat  <- round(aov_summary$`F value`[1], 4)
  p_value <- round(aov_summary$`Pr(>F)`[1],  6)

  # Eta-squared (effect size)
  ss_between <- aov_summary$`Sum Sq`[1]
  ss_total   <- sum(aov_summary$`Sum Sq`, na.rm = TRUE)
  eta_sq     <- round(ss_between / ss_total, 4)

  list(
    f_statistic     = f_stat,
    p_value         = p_value,
    significant     = p_value < 0.05,
    eta_squared     = eta_sq,
    effect_size     = ifelse(eta_sq > 0.14, "large",
                      ifelse(eta_sq > 0.06, "medium", "small")),
    interpretation  = ifelse(
      p_value < 0.05,
      paste0("Churn rates differ significantly across ", dimension,
             " segments (F=", f_stat, ", p=", p_value, ")."),
      paste0("No significant churn rate difference across ", dimension,
             " segments (p=", p_value, ").")
    )
  )
}, error = function(e) {
  list(error = paste("ANOVA failed:", e$message))
})

results$anova <- anova_result

# ── 3. Tukey HSD post-hoc (if ANOVA significant) ──────────────
if (isTRUE(anova_result$significant)) {
  cat("[R] Running Tukey HSD post-hoc...\n")

  tukey_result <- tryCatch({
    aov_model <- aov(churn_rate ~ segment_factor, data = df_dim)
    tukey     <- TukeyHSD(aov_model)$segment_factor
    tukey_df  <- as.data.frame(tukey)
    tukey_df$pair <- rownames(tukey_df)

    sig_pairs <- tukey_df[tukey_df$`p adj` < 0.05, ]

    list(
      n_significant_pairs = nrow(sig_pairs),
      significant_pairs   = lapply(1:nrow(sig_pairs), function(i) {
        list(
          pair      = sig_pairs$pair[i],
          diff      = round(sig_pairs$diff[i], 4),
          p_adj     = round(sig_pairs$`p adj`[i], 6),
          conf_low  = round(sig_pairs$lwr[i], 4),
          conf_high = round(sig_pairs$upr[i], 4)
        )
      })
    )
  }, error = function(e) {
    list(error = paste("Tukey failed:", e$message))
  })

  results$tukey_hsd <- tukey_result
}

# ── 4. Linear regression: churn_rate ~ predictors ─────────────
cat("[R] Running linear regression...\n")

reg_result <- tryCatch({
  # Use numeric predictors available in the segment data
  predictors <- intersect(
    c("segment_size", "avg_monthly_spend", "revenue_at_risk", "previous_churn_rate"),
    names(df_dim)
  )

  if (length(predictors) >= 1) {
    formula_str <- paste("churn_rate ~", paste(predictors, collapse = " + "))
    model       <- lm(as.formula(formula_str), data = df_dim)
    summ        <- summary(model)

    coef_df <- as.data.frame(summ$coefficients)
    coef_df$variable <- rownames(coef_df)

    list(
      formula        = formula_str,
      r_squared      = round(summ$r.squared, 4),
      adj_r_squared  = round(summ$adj.r.squared, 4),
      f_statistic    = round(summ$fstatistic[1], 4),
      p_value        = round(pf(summ$fstatistic[1], summ$fstatistic[2],
                                summ$fstatistic[3], lower.tail = FALSE), 6),
      coefficients   = lapply(1:nrow(coef_df), function(i) {
        list(
          variable    = coef_df$variable[i],
          estimate    = round(coef_df$Estimate[i], 6),
          std_error   = round(coef_df$`Std. Error`[i], 6),
          t_value     = round(coef_df$`t value`[i], 4),
          p_value     = round(coef_df$`Pr(>|t|)`[i], 6),
          significant = coef_df$`Pr(>|t|)`[i] < 0.05
        )
      })
    )
  } else {
    list(status = "skipped", reason = "No numeric predictors available")
  }
}, error = function(e) {
  list(error = paste("Regression failed:", e$message))
})

results$regression <- reg_result

# ── 5. Degradation significance test ──────────────────────────
# Wilcoxon test: are degrading segments significantly worse?
cat("[R] Testing degradation significance...\n")

if ("health_status" %in% names(df_dim) && "churn_rate" %in% names(df_dim)) {
  degrade_test <- tryCatch({
    degrading <- df_dim$churn_rate[df_dim$health_status == "degrading"]
    stable    <- df_dim$churn_rate[df_dim$health_status %in% c("stable", "improving")]

    if (length(degrading) >= 2 && length(stable) >= 2) {
      w_test <- wilcox.test(degrading, stable, alternative = "greater")
      list(
        test          = "Wilcoxon rank-sum (degrading > stable)",
        statistic     = round(w_test$statistic, 4),
        p_value       = round(w_test$p.value, 6),
        significant   = w_test$p.value < 0.05,
        n_degrading   = length(degrading),
        n_stable      = length(stable),
        median_degrading = round(median(degrading), 4),
        median_stable    = round(median(stable),    4),
        interpretation = ifelse(
          w_test$p.value < 0.05,
          "Degrading segments have significantly higher churn than stable segments.",
          "No statistically significant difference between degrading and stable segments."
        )
      )
    } else {
      list(status = "skipped", reason = "Not enough degrading or stable segments")
    }
  }, error = function(e) list(error = e$message))

  results$degradation_significance <- degrade_test
}

# ── 6. Summary ─────────────────────────────────────────────────
cat(sprintf("[R] ANOVA p-value: %s\n",
            ifelse(is.null(anova_result$p_value), "N/A",
                   round(anova_result$p_value, 6))))

if (!is.null(results$tukey_hsd$n_significant_pairs)) {
  cat(sprintf("[R] Tukey HSD significant pairs: %d\n",
              results$tukey_hsd$n_significant_pairs))
}

# ── Write output ───────────────────────────────────────────────
write(toJSON(results, auto_unbox = TRUE, pretty = TRUE, na = "null"),
      output_json)

cat(sprintf("[R] Results written to: %s\n", output_json))
cat("[R] segmentation_analysis.R complete.\n")
