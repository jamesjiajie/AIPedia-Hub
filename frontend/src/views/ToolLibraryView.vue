<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'
import ErrorAlert from '@/components/ErrorAlert.vue'
import ToolCard from '@/components/ToolCard.vue'
import type { CategoryRule, ClassificationPreview, TaxonomyItem, Tool, ToolPayload } from '@/types'

const route = useRoute()
const router = useRouter()
const section = computed(() => {
  if (route.name === 'quant-library') return { tag: '量化', title: '量化工具', eyebrow: '个人量化工具库', description: '保存行情、研究、回测和交易工具。', path: '/quant' }
  if (route.name === 'project-library') return { tag: '项目管理', title: '项目管理', eyebrow: '个人项目管理工具库', description: '保存协作、计划、任务与进度工具。', path: '/project-management' }
  return null
})
const tools = ref<Tool[]>([])
const categories = ref<TaxonomyItem[]>([])
const directoryTags = ref<TaxonomyItem[]>([])
const loading = ref(false)
const error = ref<unknown>(null)
const query = ref(String(route.query.q ?? ''))
const category = ref(String(route.query.category ?? ''))
const tag = ref(String(route.query.tag ?? ''))
const favoriteOnly = ref(route.query.is_favorite === 'true')
const status = ref(String(route.query.status ?? 'active'))
const sort = ref(String(route.query.sort ?? 'updated_desc'))
const total = ref(0)
const categoryName = ref('')
const renamingCategory = ref<TaxonomyItem | null>(null)
const savingCategory = ref(false)
const renamingTag = ref<TaxonomyItem | null>(null)
const tagName = ref('')
const savingTag = ref(false)
const movingToolId = ref<number | null>(null)
const categoryRules = ref<CategoryRule[]>([])
const ruleCategoryId = ref<number | null>(null)
const ruleTag = ref('')
const classificationPreview = ref<ClassificationPreview[]>([])
const showingClassification = ref(false)
const applyingClassification = ref(false)
let timer: number | undefined

const hasFilters = computed(() => Boolean(query.value || category.value || (!section.value && tag.value) || favoriteOnly.value || status.value !== 'active'))
const selectedCategoryName = computed(() => {
  if (category.value === '__uncategorized__') return '未分类'
  if (!section.value && tag.value) return directoryTags.value.find((item) => item.name === tag.value)?.name || tag.value
  return categories.value.find((item) => item.slug === category.value)?.name || (section.value ? `全部${section.value.title}` : '全部工具')
})

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  const params = new URLSearchParams({ status: status.value, sort: sort.value })
  if (query.value.trim()) params.set('q', query.value.trim())
  if (category.value) params.set('category', category.value)
  if (section.value) params.append('tag', section.value.tag)
  else if (tag.value) params.append('tag', tag.value)
  if (favoriteOnly.value) params.set('is_favorite', 'true')
  try {
    const result = await api.listTools(params)
    tools.value = result.items
    total.value = result.total
    await router.replace({ query: Object.fromEntries(params.entries()) })
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法加载工具库。')
  } finally {
    loading.value = false
  }
}

async function refreshCategories(): Promise<void> {
  categories.value = await api.listCategories()
}

async function refreshDirectoryTags(): Promise<void> {
  directoryTags.value = await api.listTags()
}

async function refreshCategoryRules(): Promise<void> {
  categoryRules.value = await api.listCategoryRules()
}

function scheduleLoad(): void {
  window.clearTimeout(timer)
  timer = window.setTimeout(load, 180)
}

function clearFilters(): void {
  query.value = ''
  category.value = ''
  if (!section.value) tag.value = ''
  favoriteOnly.value = false
  status.value = 'active'
  sort.value = 'updated_desc'
}

function selectCategory(slug = ''): void {
  tag.value = ''
  category.value = slug
}

function selectTag(name: string): void {
  if (section.value) return
  category.value = ''
  tag.value = name
}

async function saveCategory(): Promise<void> {
  const name = categoryName.value.trim()
  if (!name) return
  savingCategory.value = true
  error.value = ''
  try {
    if (renamingCategory.value) await api.renameCategory(renamingCategory.value.id, name)
    else await api.createCategory(name)
    categoryName.value = ''
    renamingCategory.value = null
    await refreshCategories()
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('分类保存失败。')
  } finally {
    savingCategory.value = false
  }
}

function startRename(item: TaxonomyItem): void {
  renamingCategory.value = item
  categoryName.value = item.name
}

async function deleteCategory(item: TaxonomyItem): Promise<void> {
  if (!window.confirm(`删除「${item.name}」后，相关工具会保留为未分类。继续吗？`)) return
  error.value = ''
  try {
    await api.deleteCategory(item.id)
    if (category.value === item.slug) selectCategory()
    await Promise.all([refreshCategories(), refreshCategoryRules(), load()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('删除分类失败。')
  }
}

function startRenameTag(item: TaxonomyItem): void {
  renamingTag.value = item
  tagName.value = item.name
}

async function saveTag(): Promise<void> {
  const name = tagName.value.trim()
  if (!renamingTag.value || !name) return
  savingTag.value = true
  error.value = ''
  try {
    await api.renameTag(renamingTag.value.id, name)
    if (tag.value === renamingTag.value.name) tag.value = name
    renamingTag.value = null
    tagName.value = ''
    await Promise.all([refreshDirectoryTags(), refreshCategoryRules(), load()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('标签保存失败。')
  } finally {
    savingTag.value = false
  }
}

async function deleteTag(item: TaxonomyItem): Promise<void> {
  if (!window.confirm(`删除标签「${item.name}」后，它会从所有工具中移除。继续吗？`)) return
  error.value = ''
  try {
    await api.deleteTag(item.id)
    if (tag.value === item.name) selectCategory()
    await Promise.all([refreshDirectoryTags(), refreshCategoryRules(), load()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('删除标签失败。')
  }
}

function toolPayload(tool: Tool, category: string | null, tags = tool.tags): ToolPayload {
  return {
    name: tool.name, aliases: tool.aliases, official_url: tool.official_url, source_url: tool.source_url,
    summary: tool.summary, why_saved: tool.why_saved, use_cases: tool.use_cases, notes: tool.notes,
    category, tags, pricing_model: tool.pricing_model, platforms: tool.platforms,
    is_favorite: tool.is_favorite, status: tool.status,
  }
}

async function moveTool(tool: Tool, category: string | null): Promise<void> {
  if (category === tool.category) return
  movingToolId.value = tool.id
  error.value = ''
  try {
    await api.updateTool(tool.id, toolPayload(tool, category))
    await Promise.all([load(), refreshCategories(), refreshDirectoryTags()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('移动工具失败。')
  } finally {
    movingToolId.value = null
  }
}

async function assignDirectory(tool: Tool, target: { type: 'category' | 'tag'; name: string } | null): Promise<void> {
  if (!target || target.type === 'category') return moveTool(tool, target?.name ?? null)
  if (tool.tags.some((item) => item.toLocaleLowerCase() === target.name.toLocaleLowerCase())) return
  movingToolId.value = tool.id
  error.value = ''
  try {
    await api.updateTool(tool.id, toolPayload(tool, tool.category, [...tool.tags, target.name]))
    await Promise.all([load(), refreshDirectoryTags()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('归入标签目录失败。')
  } finally {
    movingToolId.value = null
  }
}

async function saveCategoryRule(): Promise<void> {
  if (!ruleCategoryId.value || !ruleTag.value.trim()) return
  error.value = ''
  try {
    await api.createCategoryRule(ruleCategoryId.value, ruleTag.value.trim())
    ruleTag.value = ''
    ruleCategoryId.value = null
    await refreshCategoryRules()
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('分类规则保存失败。')
  }
}

function rulesFor(categoryId: number): CategoryRule[] {
  return categoryRules.value.filter((rule) => rule.category_id === categoryId)
}

function startAddingCategoryTag(categoryId: number): void {
  ruleCategoryId.value = categoryId
  ruleTag.value = ''
}

async function removeCategoryRule(id: number): Promise<void> {
  error.value = ''
  try {
    await api.deleteCategoryRule(id)
    await refreshCategoryRules()
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('删除分类规则失败。')
  }
}

async function showClassificationPreview(): Promise<void> {
  error.value = ''
  try {
    classificationPreview.value = await api.classificationPreview()
    showingClassification.value = true
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法生成归类预览。')
  }
}

async function applyClassification(): Promise<void> {
  const decisions = classificationPreview.value
    .filter((item) => item.suggested_category_id)
    .map((item) => ({ tool_id: item.tool_id, category_id: item.suggested_category_id! }))
  if (!decisions.length) return
  applyingClassification.value = true
  error.value = ''
  try {
    await api.applyClassification(decisions)
    classificationPreview.value = []
    await Promise.all([load(), refreshCategories()])
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('批量归类失败。')
  } finally {
    applyingClassification.value = false
  }
}

watch(section, () => {
  query.value = ''
  category.value = ''
  tag.value = ''
  favoriteOnly.value = false
  status.value = 'active'
  sort.value = 'updated_desc'
})

watch([query, category, tag, favoriteOnly, status, sort, section], scheduleLoad)

onMounted(async () => {
  await Promise.all([refreshCategories().catch(() => []), refreshDirectoryTags().catch(() => []), refreshCategoryRules().catch(() => [])])
  await load()
})
</script>

<template>
  <section class="page library-page">
    <div class="library-heading">
      <div>
        <p class="eyebrow">{{ section?.eyebrow || '个人 AI 工具记忆库' }}</p>
        <div class="library-title-row"><h1>{{ section?.title || '工具库' }}</h1><span>{{ total }} 个工具</span></div>
        <p class="subtle">{{ section?.description || '保存工具，也保存它对你有意义的理由。' }}</p>
      </div>
      <RouterLink class="button button-primary" :to="section ? `${section.path}/tools/new` : '/tools/new'">添加{{ section?.title || '' }}工具</RouterLink>
    </div>

    <div class="library-layout">
      <aside class="category-directory" aria-label="工具分类目录">
        <div class="directory-heading"><h2>目录</h2></div>
        <p class="directory-label">浏览</p>
        <button class="directory-item" :class="{ active: !category && !tag }" type="button" @click="selectCategory()"><span>全部工具</span><small>{{ total }}</small></button>
        <button class="directory-item" :class="{ active: category === '__uncategorized__' }" type="button" @click="selectCategory('__uncategorized__')"><span>未分类</span><small>待整理</small></button>
        <p class="directory-label directory-label-spaced">分类与标签</p>
        <div class="directory-list">
          <div v-for="item in categories" :key="item.id" class="directory-entry">
            <div class="directory-row">
              <button class="directory-item" :class="{ active: category === item.slug }" type="button" @click="selectCategory(item.slug)"><span>{{ item.name }}</span><small>{{ item.usage_count }}</small></button>
              <button class="directory-edit" type="button" :aria-label="`重命名 ${item.name}`" @click="startRename(item)">⋯</button>
            </div>
            <form v-if="renamingCategory?.id === item.id" class="category-rule-editor" @submit.prevent="saveCategory">
              <input v-model="categoryName" maxlength="100" placeholder="新的分类名称" autofocus />
              <button class="text-button" type="submit" :disabled="savingCategory">保存</button>
              <button class="text-button danger-button" type="button" @click="deleteCategory(item)">删除</button>
              <button class="text-button" type="button" @click="renamingCategory = null; categoryName = ''">取消</button>
            </form>
          </div>
          <template v-if="!section">
            <div v-for="item in directoryTags" :key="`tag-${item.id}`" class="directory-entry">
              <div class="directory-row">
                <button class="directory-item directory-tag-item" :class="{ active: tag === item.name }" type="button" @click="selectTag(item.name)"><span>{{ item.name }}</span><small>{{ item.usage_count }}</small></button>
                <button class="directory-edit" type="button" :aria-label="`修改 ${item.name}`" @click="startRenameTag(item)">⋯</button>
              </div>
              <form v-if="renamingTag?.id === item.id" class="category-rule-editor" @submit.prevent="saveTag">
                <input v-model="tagName" maxlength="100" placeholder="新的标签名称" autofocus />
                <button class="text-button" type="submit" :disabled="savingTag">保存</button>
                <button class="text-button danger-button" type="button" @click="deleteTag(item)">删除</button>
                <button class="text-button" type="button" @click="renamingTag = null; tagName = ''">取消</button>
              </form>
            </div>
          </template>
        </div>
        <details v-if="!section" class="directory-management">
          <summary>整理分类与标签</summary>
          <form class="category-form" @submit.prevent="saveCategory">
            <input v-model="categoryName" placeholder="新建分类名称" maxlength="100" />
            <button class="text-button" type="submit" :disabled="savingCategory">+ 新建分类</button>
          </form>
          <div v-for="item in categories" :key="`rule-${item.id}`" class="rule-manager">
            <strong>{{ item.name }}</strong>
            <div class="directory-tags">
              <button v-for="rule in rulesFor(item.id)" :key="rule.id" type="button" :aria-label="`删除标签 ${rule.tag_name}`" @click="removeCategoryRule(rule.id)">{{ rule.tag_name }} ×</button>
              <button type="button" @click="startAddingCategoryTag(item.id)">+ 标签</button>
            </div>
            <form v-if="ruleCategoryId === item.id" class="category-rule-editor" @submit.prevent="saveCategoryRule">
              <input v-model="ruleTag" maxlength="100" placeholder="输入用于归类的标签" autofocus />
              <button class="text-button" type="submit">添加</button>
              <button class="text-button" type="button" @click="ruleCategoryId = null; ruleTag = ''">取消</button>
            </form>
          </div>
          <button class="directory-preview" type="button" @click="showClassificationPreview">按目录标签预览归类</button>
        </details>
      </aside>
      <div class="library-content">
        <section v-if="!section && showingClassification" class="classification-panel">
          <div><h2>按标签归类预览</h2><p>只显示尚未分类的活跃工具；多个类别命中时保留待选择。</p></div>
          <button class="text-button" type="button" @click="showingClassification = false">关闭</button>
          <div v-if="classificationPreview.length" class="classification-list"><div v-for="item in classificationPreview" :key="item.tool_id"><strong>{{ item.tool_name }}</strong><span>命中：{{ item.matched_tags.join('、') }}</span><span>{{ item.suggested_category_name ? `建议归入「${item.suggested_category_name}」` : '命中多个分类，请手动选择' }}</span></div></div>
          <p v-else>没有可自动归类的未分类工具。</p>
          <button v-if="classificationPreview.some((item) => item.suggested_category_id)" class="button button-primary" type="button" :disabled="applyingClassification" @click="applyClassification">{{ applyingClassification ? '归类中…' : '应用明确建议' }}</button>
        </section>
        <section class="search-panel" aria-label="搜索和筛选">
          <input v-model="query" class="search-input" type="search" :placeholder="`在${selectedCategoryName}中搜索名称、标签或备注…`" />
          <div class="filter-row">
            <select v-model="status" aria-label="状态">
              <option value="active">活跃工具</option>
              <option value="archived">已归档</option>
              <option value="unavailable">不可用</option>
            </select>
            <select v-model="sort" aria-label="排序">
              <option value="updated_desc">最近更新</option>
              <option value="created_desc">最近添加</option>
              <option value="viewed_desc">最近查看</option>
              <option value="name_asc">按名称</option>
            </select>
            <label class="checkbox-row"><input v-model="favoriteOnly" type="checkbox" /> 仅收藏</label>
            <button v-if="hasFilters" class="text-button" type="button" @click="clearFilters">清除筛选</button>
          </div>
        </section>

        <div class="result-meta"><h2>{{ selectedCategoryName }}</h2><span>{{ loading ? '正在搜索…' : `${total} 个工具` }}</span></div>
        <ErrorAlert v-if="error" :error="error" />

        <div v-if="!loading && tools.length" class="tool-grid">
          <ToolCard v-for="tool in tools" :key="tool.id" :tool="tool" :categories="categories" :tags="directoryTags" :moving="movingToolId === tool.id" @assign="assignDirectory(tool, $event)" />
        </div>
        <div v-else-if="!loading" class="empty-state">
          <h2>{{ hasFilters ? '没有匹配的工具' : '你的工具库还是空的' }}</h2>
          <p>{{ hasFilters ? '换个关键词或减少筛选条件试试。' : '从下一个让你眼前一亮的 AI 工具开始。' }}</p>
          <RouterLink v-if="!hasFilters" class="button button-primary" :to="section ? `${section.path}/tools/new` : '/tools/new'">记录第一个{{ section?.title || '' }}工具</RouterLink>
        </div>
      </div>
    </div>
  </section>
</template>
