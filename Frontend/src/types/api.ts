export interface HealthResponse {
  status: 'ok' | 'degraded'
  db_connected: boolean
  model_loaded: boolean
  version: string
  uptime_s: number
}

export type RiskTier = 'Critical' | 'High' | 'Medium' | 'Safe'
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW'
export type HealthStatus = 'degrading' | 'stable' | 'improving'
export type DriftSeverity = 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE'

export interface PredictionOut {
  customer_id: string
  churn_probability: number
  risk_tier: RiskTier
  model_name?: string
  predicted_at?: string
}

export interface BatchPredictionOut {
  predictions: PredictionOut[]
  n_customers: number
  churn_rate: number
  risk_summary: Record<RiskTier, number>
}

export interface FeatureExplanation {
  feature: string
  importance: number
  direction: 'risk+' | 'risk-'
  confidence: ConfidenceLevel
}

export interface ExplanationOut {
  customer_id: string
  churn_probability: number
  primary_method: string
  validators_active: number
  high_conf_features: string[]
  explanations: FeatureExplanation[]
  reasoning?: Record<string, unknown>
}

export interface SegmentOut {
  segment_id: string
  dimension: string
  value: string
  churn_rate?: number
  previous_churn_rate?: number
  churn_delta?: number
  health_status?: HealthStatus
  risk_level?: string
  revenue_at_risk?: number
  acceleration?: string
  exceeds_benchmark?: boolean
}

export interface GlobalInsights {
  top_degrading_segments: SegmentOut[]
  top_improving_segments: SegmentOut[]
  accelerating_risk_segments: SegmentOut[]
  total_revenue_at_risk: number
  n_degrading: number
  n_improving: number
  n_stable: number
  n_accelerating: number
}

export interface SegmentsResponse {
  run_id?: string
  n_segments: number
  segments: SegmentOut[]
  global_insights?: GlobalInsights
}

export interface DriftFeatureOut {
  feature: string
  psi?: number
  psi_status?: string
  ks_statistic?: number
  p_value?: number
  drift_severity?: DriftSeverity
  trend?: string
  velocity?: string
  early_warning: boolean
  xai_confirmed: boolean
}

export interface DriftResponse {
  overall_severity: DriftSeverity
  n_features_tracked: number
  drifted_features: string[]
  early_warnings: DriftFeatureOut[]
  retraining_trigger: {
    model_retraining_required: boolean
    reason: string
    features_above_threshold?: string[]
  }
  drift_features: DriftFeatureOut[]
}

export interface InsightResponse {
  executive_summary: string
  customer_risk: Record<string, unknown>
  segments: Record<string, unknown>
  drift_analysis: Record<string, unknown>
  causal_analysis: Record<string, unknown>
  prediction_outlook: Record<string, unknown>
  recommendations: Array<{
    rank: number
    description: string
    target: string
    source: string
  }>
  business_impact: {
    total_annual_revenue_at_risk: number
    projected_loss_if_no_action: number
    potential_recovery: number
    critical_customers_count: number
    high_risk_customers_count: number
  }
  generated_at?: string
  llm_mode?: string
}

export interface ModelOut {
  model_name: string
  val_auc?: number
  val_f1?: number
  test_auc?: number
  test_f1?: number
  n_features?: number
  xai_method?: string
  is_active: boolean
  trained_at?: string
}

export interface LeaderboardResponse {
  best_model?: ModelOut
  all_models: ModelOut[]
  n_models: number
}

export interface CustomerRiskOut {
  customer_id: string
  churn_probability: number
  risk_tier: RiskTier
  plan_type?: string
  region?: string
  contract_type?: string
  primary_driver?: string
  top_action?: string
}

export interface CustomerProfileOut {
  customer_id: string
  profile: Record<string, unknown>
  prediction?: PredictionOut
  explanation?: ExplanationOut
  segment?: SegmentOut
  insights?: Record<string, unknown>
}


export interface WatchlistResponse {
  threshold: number
  n_customers: number
  customers: Array<Record<string, unknown>>
}

export interface UploadResponse {
  upload_id: string
  filename: string
  rows_ingested?: number
  churn_rate?: number
  status: string
  job_id?: string
}

export interface PipelineStatusResponse {
  run_id: string
  status: 'queued' | 'running' | 'done' | 'failed'
  phases_run?: string[]
  n_customers?: number
  runtime_seconds?: number
  error_msg?: string
  started_at?: string
  completed_at?: string
}

export interface QAResponse {
  question: string
  answer: string
  intent: string
  source: 'llm' | 'rules'
  context_used: string[]
}
