import type { CategoryRule, ClassificationPreview, CrawlJob, DiscoverySource, TaxonomyItem, Tool, ToolDraft, ToolListResponse, ToolPayload } from '@/types'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
    readonly detail: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function describeError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback
  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (!item || typeof item !== 'object') return String(item)
      const value = item as { loc?: unknown; msg?: unknown }
      const location = Array.isArray(value.loc) ? value.loc.join('.') : '请求参数'
      return `${location}: ${typeof value.msg === 'string' ? value.msg : '格式不正确'}`
    }).join('\n')
  }
  if (detail && typeof detail === 'object' && typeof (detail as { message?: unknown }).message === 'string') {
    return (detail as { message: string }).message
  }
  return fallback
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch (reason) {
    const detail = reason instanceof Error ? reason.message : '浏览器无法连接到服务。'
    throw new ApiError('无法连接到服务。', 0, path, detail)
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = describeError(payload, response.statusText || '服务未返回可识别的错误说明。')
    throw new ApiError(`请求失败（HTTP ${response.status}）。`, response.status, path, detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  listTools(params: URLSearchParams) {
    const search = params.toString()
    return request<ToolListResponse>(`/tools${search ? `?${search}` : ''}`)
  },
  getTool(id: string | number) {
    return request<Tool>(`/tools/${id}`)
  },
  createTool(payload: ToolPayload) {
    return request<Tool>('/tools', { method: 'POST', body: JSON.stringify(payload) })
  },
  updateTool(id: string | number, payload: ToolPayload) {
    return request<Tool>(`/tools/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
  },
  archiveTool(id: string | number) {
    return request<Tool>(`/tools/${id}/archive`, { method: 'POST' })
  },
  restoreTool(id: string | number) {
    return request<Tool>(`/tools/${id}/restore`, { method: 'POST' })
  },
  buildToolDraft(payload: { tool_name: string; user_hint: string | null; sources: DiscoverySource[] }) {
    return request<ToolDraft>('/discovery/draft', { method: 'POST', body: JSON.stringify(payload) })
  },
  startCrawl(payload: { tool_name: string; official_url: string | null; source_url: string | null; user_hint: string | null }) {
    return request<CrawlJob>('/discovery/crawl', { method: 'POST', body: JSON.stringify(payload) })
  },
  getCrawl(jobId: string) {
    return request<CrawlJob>(`/discovery/crawl/${jobId}`)
  },
  listCategories() {
    return request<TaxonomyItem[]>('/categories')
  },
  createCategory(name: string) {
    return request<TaxonomyItem>('/categories', { method: 'POST', body: JSON.stringify({ name }) })
  },
  renameCategory(id: number, name: string) {
    return request<TaxonomyItem>(`/categories/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) })
  },
  deleteCategory(id: number) {
    return request<void>(`/categories/${id}`, { method: 'DELETE' })
  },
  listCategoryRules() {
    return request<CategoryRule[]>('/category-rules')
  },
  createCategoryRule(categoryId: number, tagName: string) {
    return request<CategoryRule>('/category-rules', { method: 'POST', body: JSON.stringify({ category_id: categoryId, tag_name: tagName }) })
  },
  deleteCategoryRule(id: number) {
    return request<void>(`/category-rules/${id}`, { method: 'DELETE' })
  },
  classificationPreview() {
    return request<ClassificationPreview[]>('/classification-preview')
  },
  applyClassification(decisions: Array<{ tool_id: number; category_id: number }>) {
    return request<Tool[]>('/classify', { method: 'POST', body: JSON.stringify({ decisions }) })
  },
  listTags() {
    return request<TaxonomyItem[]>('/tags')
  },
  renameTag(id: number, name: string) {
    return request<TaxonomyItem>(`/tags/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) })
  },
  deleteTag(id: number) {
    return request<void>(`/tags/${id}`, { method: 'DELETE' })
  },
}
