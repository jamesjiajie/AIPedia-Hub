export type PricingModel = 'unknown' | 'free' | 'freemium' | 'paid' | 'open_source'
export type ToolStatus = 'active' | 'archived' | 'unavailable'

export interface ToolPayload {
  name: string
  aliases: string[]
  official_url: string | null
  source_url: string | null
  summary: string | null
  why_saved: string | null
  use_cases: string | null
  notes: string | null
  category: string | null
  tags: string[]
  pricing_model: PricingModel
  platforms: string[]
  is_favorite: boolean
  status: ToolStatus
}

export interface Tool extends ToolPayload {
  id: number
  slug: string
  canonical_url: string | null
  created_at: string
  updated_at: string
  last_viewed_at: string | null
}

export interface ToolListResponse {
  items: Tool[]
  page: number
  page_size: number
  total: number
}

export interface TaxonomyItem {
  id: number
  name: string
  slug: string
  usage_count: number
}

export interface DiscoverySource {
  url: string
  title: string | null
  source_type: string
  excerpt: string
}

export interface FieldEvidence {
  field: string
  source_url: string
  quote: string | null
  confidence: string
}

export interface ToolDraft {
  tool: ToolPayload
  field_evidence: FieldEvidence[]
  unsupported_fields: string[]
  review_needed: boolean
  research_summary: string | null
}

export interface CrawlJob {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  draft: ToolDraft | null
  error: string | null
  events: CrawlEvent[]
}

export interface CrawlEvent {
  at: string
  level: 'info' | 'success' | 'error'
  message: string
}

export const emptyTool = (): ToolPayload => ({
  name: '',
  aliases: [],
  official_url: null,
  source_url: null,
  summary: null,
  why_saved: null,
  use_cases: null,
  notes: null,
  category: null,
  tags: [],
  pricing_model: 'unknown',
  platforms: [],
  is_favorite: false,
  status: 'active',
})
