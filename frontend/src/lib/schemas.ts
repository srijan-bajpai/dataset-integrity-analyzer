import { z } from 'zod';

export const DatasetRunSummarySchema = z.object({
  id: z.string(),
  status: z.string(),
  created_at: z.string().nullable().optional(),
}).passthrough();

export const DatasetSchema = z.object({
  id: z.string(),
  name: z.string(),
  layout: z.string().default('folder_per_class'),
  fingerprint: z.string().nullable().optional(),
  sample_count: z.number().default(0),
  class_count: z.number().default(0),
  classes: z.array(z.string()).default([]),
  status: z.string().default('ingested'),
  created_at: z.string().nullable().optional(),
  description: z.string().optional(),
}).passthrough();

export const DatasetDetailSchema = DatasetSchema.extend({
  runs: z.array(DatasetRunSummarySchema).default([]),
}).passthrough();

export const DatasetListSchema = z.array(DatasetSchema);

export const RunSchema = z.object({
  id: z.string(),
  dataset_id: z.string(),
  status: z.enum(['queued', 'running', 'completed', 'failed', 'cancelled']),
  created_at: z.string().nullable().optional(),
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  progress_percent: z.number().default(0),
  status_message: z.string().default('Queued'),
  duration_seconds: z.number().nullable().optional(),
  error_message: z.string().nullable().optional(),
  report_url: z.string().nullable().optional(),
}).passthrough();

export const DimensionScoreItemSchema = z.object({
  score: z.number().default(0),
  status: z.string().default('available'),
  weight: z.number().default(1),
}).passthrough();

export const ReadinessScoreSchema = z.object({
  overall_score: z.number().default(0),
  verdict: z.string().default('Needs Remediation'),
  coverage_pct: z.number().optional(),
  dimension_scores: z.record(DimensionScoreItemSchema).default({}),
  hard_gates_tripped: z.array(z.string()).optional(),
}).passthrough();

export const ConfoundInteractionSchema = z.object({
  code: z.string().optional(),
  type: z.string().optional(),
  name: z.string().optional(),
  variable_a: z.string().optional(),
  variable_b: z.string().optional(),
  dimension_a: z.string().optional(),
  dimension_b: z.string().optional(),
  status: z.string().default('verified_safe'),
  severity: z.string().optional(),
  statistic: z.number().nullable().optional(),
  p_value_raw: z.number().nullable().optional(),
  p_value_corrected: z.number().nullable().optional(),
  effect_size_epsilon_squared: z.number().nullable().optional(),
  effect_size_cramers_v: z.number().nullable().optional(),
  effect_size: z.number().nullable().optional(),
  p_value: z.number().nullable().optional(),
  q_value: z.number().nullable().optional(),
  description: z.string().default(''),
  downstream_consequence: z.string().optional(),
  plain_english_explanation: z.string().optional(),
  remedy_suggestion: z.string().optional(),
  affected_group: z.string().optional(),
  affected_sample_count: z.number().optional(),
  duplicate_rate: z.number().optional(),
  disagreement_rate: z.number().optional(),
  leaked_sample_count: z.number().optional(),
}).passthrough();

export const RecommendationSchema = z.object({
  category: z.string().default(''),
  action_type: z.string().default(''),
  priority: z.string().default('Medium'),
  defect: z.string().default(''),
  affected_sample_count: z.number().default(0),
  projected_score_gain: z.number().default(0),
  estimated_effort: z.string().default('Medium'),
  machine_actionable: z.boolean().default(false),
  rationale: z.string().default(''),
  action: z.string().default(''),
  trade_off_risk: z.string().default(''),
  gain_per_effort: z.number().optional(),
  do_first: z.boolean().optional(),
  rank: z.number().optional(),
}).passthrough();

export const ManifestItemSchema = z.object({
  sample_ref: z.string(),
  action: z.string(),
  target_dimension: z.string().default(''),
  reason: z.string().default(''),
  current_label: z.string().nullable().optional(),
  suggested_value: z.string().nullable().optional(),
  gain_estimate: z.number().optional(),
}).passthrough();

export const ReportSchema = z.object({
  report_version: z.string().default('dia-report-v2'),
  dataset_fingerprint: z.string().default(''),
  sample_count: z.number().default(0),
  readable_sample_count: z.number().default(0),
  analyzed_sample_count: z.number().default(0),
  sampling: z.object({
    requested_rate: z.number().default(1.0),
    actual_rate: z.number().default(1.0),
    seed: z.number().default(42),
    strategy: z.string().default('stratified'),
  }).passthrough().default({}),
  results: z.object({
    readiness: ReadinessScoreSchema.default({ overall_score: 0, verdict: 'Needs Remediation', dimension_scores: {} }),
    distribution: z.record(z.any()).optional(),
    fairness: z.record(z.any()).optional(),
    quality: z.record(z.any()).optional(),
    duplicates: z.record(z.any()).optional(),
    diversity: z.record(z.any()).optional(),
    labels: z.record(z.any()).optional(),
    confounds: z.object({
      detected_confounds: z.array(ConfoundInteractionSchema).default([]),
      tested_confounds: z.array(z.string()).default([]),
      absent_confounds: z.array(z.string()).default([]),
      status: z.string().optional(),
      correction: z.string().optional(),
    }).passthrough().optional(),
    bias_impact: z.record(z.any()).optional(),
    recommendations: z.array(RecommendationSchema).optional(),
  }).passthrough().default({}),
  findings: z.array(z.object({
    code: z.string(),
    severity: z.string().default('warning'),
    count: z.number().optional(),
    description: z.string().default(''),
  }).passthrough()).default([]),
  sample_findings: z.array(z.record(z.any())).default([]),
  remediation_manifest: z.array(ManifestItemSchema).default([]),
}).passthrough();

export const WhatIfResponseSchema = z.object({
  run_id: z.string(),
  baseline_score: z.number().nullable().optional(),
  what_if_score: z.number().default(0),
  score_delta: z.number().nullable().default(0),
  readiness: ReadinessScoreSchema,
  changes: z.record(z.number()).default({}),
  interpretation: z.string().default(''),
}).passthrough();

export const FlaggedSampleSchema = z.object({
  sample_ref: z.string(),
  ground_truth_class: z.string().nullable().default(null),
  split: z.string().default('unspecified'),
  attributes: z.record(z.any()).default({}),
  inferred_attributes: z.record(z.any()).default({}),
  flags: z.array(z.string()).default([]),
  metrics: z.record(z.any()).default({}),
});

export const FlaggedSamplesListSchema = z.object({
  total: z.number().default(0),
  items: z.array(FlaggedSampleSchema).default([]),
});

export const Point3DSchema = z.object({
  sample_ref: z.string(),
  ground_truth_class: z.string().default('unlabelled'),
  split: z.string().default('unspecified'),
  cluster_id: z.number().default(0),
  x: z.number().default(0),
  y: z.number().default(0),
  z: z.number().default(0),
  is_outlier: z.boolean().default(false),
  outlier_score: z.number().default(0),
});

export const Embeddings3DSchema = z.object({
  run_id: z.string(),
  has_real_embeddings: z.boolean().default(false),
  sample_count: z.number().default(0),
  variance_explained: z.tuple([z.number(), z.number(), z.number()]).default([0, 0, 0]),
  points: z.array(Point3DSchema).default([]),
});

export const RunComparisonSchema = z.object({
  run_a: z.string(),
  run_b: z.string(),
  dataset_fingerprints: z.array(z.string().nullable()).default([]),
  same_dataset_fingerprint: z.boolean().default(false),
  readiness_score_delta_b_minus_a: z.number().nullable().default(null),
  class_count_deltas_b_minus_a: z.record(z.number()).default({}),
  interpretation: z.string().default(''),
}).passthrough();
