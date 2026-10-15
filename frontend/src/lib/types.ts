export type RunStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Dataset {
  id: string;
  name: string;
  layout: string;
  fingerprint: string | null;
  sample_count: number;
  class_count: number;
  classes: string[];
  status: string;
  created_at: string | null;
  description?: string;
}

export interface DatasetRunSummary {
  id: string;
  status: string;
  created_at?: string | null;
}

export interface DatasetDetail extends Dataset {
  runs: DatasetRunSummary[];
}

export interface AnalysisRun {
  id: string;
  dataset_id: string;
  status: RunStatus;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  progress_percent: number;
  status_message: string;
  duration_seconds: number | null;
  error_message: string | null;
  report_url: string | null;
}

export interface ReadinessScore {
  overall_score: number;
  verdict: 'Production Ready' | 'Acceptable' | 'Needs Remediation' | 'Critical / Not Ready';
  coverage_pct?: number;
  dimension_scores: {
    distribution?: { score: number; status: string; weight: number };
    fairness?: { score: number; status: string; weight: number };
    quality?: { score: number; status: string; weight: number };
    duplicates?: { score: number; status: string; weight: number };
    diversity?: { score: number; status: string; weight: number };
    labels?: { score: number; status: string; weight: number };
    [key: string]: { score: number; status: string; weight: number } | undefined;
  };
  hard_gates_tripped?: string[];
}

export interface ConfoundInteraction {
  code?: string;
  type?: string;
  name?: string;
  variable_a?: string;
  variable_b?: string;
  dimension_a?: string;
  dimension_b?: string;
  status: 'significant_risk' | 'verified_safe' | 'limited_data' | string;
  severity?: 'critical' | 'warning' | 'review' | string;
  statistic?: number | null;
  p_value_raw?: number | null;
  p_value_corrected?: number | null;
  effect_size_epsilon_squared?: number | null;
  effect_size_cramers_v?: number | null;
  effect_size?: number | null;
  p_value?: number | null;
  q_value?: number | null;
  description?: string;
  downstream_consequence?: string;
  plain_english_explanation?: string;
  remedy_suggestion?: string;
  affected_group?: string;
  affected_sample_count?: number;
  duplicate_rate?: number;
  disagreement_rate?: number;
  leaked_sample_count?: number;
}

export interface RecommendationItem {
  category: string;
  action_type: string;
  priority: string;
  defect: string;
  affected_sample_count: number;
  projected_score_gain: number;
  estimated_effort: string;
  machine_actionable: boolean;
  rationale: string;
  action: string;
  trade_off_risk: string;
  gain_per_effort?: number;
  do_first?: boolean;
  rank?: number;
}

export interface RecommendationManifestItem {
  sample_ref: string;
  action: 'REMOVE_DUPLICATE' | 'RELABEL_SAMPLE' | 'INSPECT_DEFECT' | 'AUGMENT_CLASS' | string;
  target_dimension: string;
  reason: string;
  current_label?: string | null;
  suggested_value?: string | null;
  gain_estimate?: number;
}

export interface RemediationTopAction {
  title: string;
  dimension: string;
  score_gain_pts: number;
  affected_count: number;
  action_type: string;
  description: string;
  plain_english: string;
}

export interface ReportData {
  report_version: string;
  dataset_fingerprint: string;
  sample_count: number;
  readable_sample_count: number;
  analyzed_sample_count: number;
  sampling: {
    requested_rate: number;
    actual_rate: number;
    seed: number;
    strategy: string;
  };
  results: {
    readiness: ReadinessScore;
    distribution?: {
      imbalance_ratio?: number;
      class_counts?: Record<string, number>;
      gini_coefficient?: number;
    };
    fairness?: {
      worst_absolute_target_gap?: number;
      group_proportions?: Record<string, Record<string, number>>;
    };
    quality?: {
      defect_rate_pct?: number;
      blur_defects?: number;
      underexposed_defects?: number;
      overexposed_defects?: number;
      low_contrast_defects?: number;
      low_res_defects?: number;
    };
    duplicates?: {
      redundancy_ratio?: number;
      near_duplicate_count?: number;
      cross_split_duplicate_groups?: number;
      conflicting_label_duplicate_groups?: number;
      duplicate_groups?: Array<{
        group_id: number;
        sample_refs: string[];
        splits: string[];
        labels: string[];
      }>;
    };
    diversity?: {
      cluster_entropy?: number;
      selected_k?: number;
      silhouette_score?: number | null;
      dbscan?: {
        noise_count?: number;
        noise_rate?: number;
      };
      per_class?: Record<string, {
        cluster_entropy: number;
        mean_pairwise_cosine_distance: number;
        low_diversity: boolean;
      }>;
    };
    labels?: {
      label_noise_rate_pct?: number;
      noise_matrix?: Record<string, Record<string, number>>;
      suspected_mislabel_count?: number;
    };
    confounds?: {
      detected_confounds?: ConfoundInteraction[];
      tested_confounds?: string[];
      absent_confounds?: string[];
      status?: string;
      correction?: string;
    };
    bias_impact?: {
      enabled: boolean;
      estimated_accuracy_loss_pct?: number;
      uncertainty_margin_pct?: number;
      worst_affected_subgroup?: string;
      projected_recovered_accuracy_pct?: number;
    };
    recommendations?: RecommendationItem[];
  };
  findings: Array<{
    code: string;
    severity: 'critical' | 'high' | 'warning' | 'review' | 'info';
    count?: number;
    description: string;
  }>;
  sample_findings: Array<{
    sample_ref: string;
    ground_truth_class?: string;
    flags: string[];
    predicted_class?: string;
    label_issue_prob?: number;
    duplicate_group?: number;
    outlier_score?: number;
  }>;
  remediation_manifest: RecommendationManifestItem[];
}

export interface WhatIfResponse {
  run_id: string;
  baseline_score: number;
  what_if_score: number;
  score_delta: number;
  readiness: ReadinessScore;
  changes: Record<string, number>;
  interpretation: string;
}

export interface FlaggedSampleItem {
  sample_ref: string;
  ground_truth_class: string | null;
  split: string;
  attributes: Record<string, unknown>;
  inferred_attributes: Record<string, unknown>;
  flags: string[];
  metrics: Record<string, unknown>;
}

export interface Point3D {
  sample_ref: string;
  ground_truth_class: string;
  split: string;
  cluster_id: number;
  x: number;
  y: number;
  z: number;
  is_outlier: boolean;
  outlier_score: number;
}

export interface Embeddings3DResponse {
  run_id: string;
  has_real_embeddings: boolean;
  sample_count: number;
  variance_explained: [number, number, number];
  points: Point3D[];
}

export interface RunComparison {
  run_a: string;
  run_b: string;
  dataset_fingerprints: (string | null)[];
  same_dataset_fingerprint: boolean;
  readiness_score_delta_b_minus_a: number | null;
  class_count_deltas_b_minus_a: Record<string, number>;
  interpretation: string;
}
