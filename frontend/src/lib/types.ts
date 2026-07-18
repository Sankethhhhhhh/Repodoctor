export interface StructuredRuleResult {
  rule: string
  status: string
  severity?: string
  evidence: string
  recommendation?: string
  documentation?: string | null
  points?: number
  max_points?: number
}

export interface CategoryScore {
  name: string
  score: number
  max_score: number
  details?: StructuredRuleResult[]
}

export interface ReportSummary {
  overall_percentage: number
  grade: string
  passed_rules: number
  failed_rules: number
  total_rules: number
  categories_passed: number
  categories_failed: number
}

export interface ReportResponse {
  id: string
  repo_name: string
  repo_url: string
  owner: string
  score: number
  grade: string
  summary: ReportSummary
  categories: CategoryScore[]
  recommendations: string[]
  created_at: string
  debug?: DebugInfo | null
}

export interface DebugInfo {
  rules_evaluated: number
  github_files_inspected: number
  github_api_calls: string[]
  scoring_details: { rule: string; status: string; points: number; max_points: number; evidence: string; severity: string }[]
  repo_metadata: Record<string, unknown>
}

export interface ReportListItem {
  id: string
  repo_name: string
  repo_url: string
  score: number
  grade: string
  created_at: string
}

export interface ReportListResponse {
  reports: ReportListItem[]
  total: number
}

export interface AnalyzeRequest {
  url: string
}

export interface CompareRequest {
  report_id_a: string
  report_id_b: string
}

export interface CategoryComparison {
  name: string
  score_a: number
  score_b: number
  max_score: number
  winner: string
}

export interface CompareResponse {
  report_a: { id: string; repo_name: string; score: number; grade: string; categories: { name: string; score: number; max_score: number }[] }
  report_b: { id: string; repo_name: string; score: number; grade: string; categories: { name: string; score: number; max_score: number }[] }
  overall_winner: string
  score_difference: number
  category_comparison: CategoryComparison[]
  improvement_suggestions: string[]
}
