export interface Task {
  id: number
  name: string
  status: string
  progress: number
  current_stage: number
  stages: Array<{
    id: number
    number: number
    type: string
    name: string
    status: string
    progress: number
  }>
}

export interface AnalysisResult {
  type: 'image' | 'text' | 'final'
  url?: string
  content?: string
  description?: string
  timestamp: number
  summary?: {
    total_objects: number
    total_layers: number
    total_text_annotations: number
    total_symbols: number
    map_scale: string
    coverage_area: string
  }
  issues?: Array<{
    type: 'warning' | 'error'
    message: string
  }>
  recommendations?: string[]
}

export interface ReviewResult {
  type: 'image' | 'text' | 'final'
  url?: string
  content?: string
  description?: string
  timestamp: number
  summary?: {
    total_issues: number
    total_fixed: number
    total_pending: number
    total_ignored: number
    review_score: number
    review_status: 'passed' | 'failed' | 'pending'
  }
  issues?: Array<{
    type: 'warning' | 'error'
    message: string
    status: 'fixed' | 'pending' | 'ignored'
  }>
  recommendations?: string[]
} 