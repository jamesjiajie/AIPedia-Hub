<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'
import ErrorAlert from '@/components/ErrorAlert.vue'
import ToolCard from '@/components/ToolCard.vue'
import type { TaxonomyItem, Tool } from '@/types'

const route = useRoute()
const router = useRouter()
const tools = ref<Tool[]>([])
const categories = ref<TaxonomyItem[]>([])
const loading = ref(false)
const error = ref<unknown>(null)
const query = ref(String(route.query.q ?? ''))
const category = ref(String(route.query.category ?? ''))
const favoriteOnly = ref(route.query.is_favorite === 'true')
const status = ref(String(route.query.status ?? 'active'))
const sort = ref(String(route.query.sort ?? 'updated_desc'))
const total = ref(0)
let timer: number | undefined

const hasFilters = computed(() => Boolean(query.value || category.value || favoriteOnly.value || status.value !== 'active'))

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  const params = new URLSearchParams({ status: status.value, sort: sort.value })
  if (query.value.trim()) params.set('q', query.value.trim())
  if (category.value) params.set('category', category.value)
  if (favoriteOnly.value) params.set('is_favorite', 'true')
  try {
    const result = await api.listTools(params)
    tools.value = result.items
    total.value = result.total
    await router.replace({ query: Object.fromEntries(params) })
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法加载工具库。')
  } finally {
    loading.value = false
  }
}

function scheduleLoad(): void {
  window.clearTimeout(timer)
  timer = window.setTimeout(load, 180)
}

function clearFilters(): void {
  query.value = ''
  category.value = ''
  favoriteOnly.value = false
  status.value = 'active'
  sort.value = 'updated_desc'
}

watch([query, category, favoriteOnly, status, sort], scheduleLoad)

onMounted(async () => {
  categories.value = await api.listCategories().catch(() => [])
  await load()
})
</script>

<template>
  <section class="page library-page">
    <div class="hero-row">
      <div>
        <p class="eyebrow">个人 AI 工具记忆库</p>
        <h1>以后想不起名字，也能找回当时的灵感。</h1>
        <p class="subtle">保存工具，也保存它对你有意义的理由。</p>
      </div>
      <RouterLink class="button button-primary" to="/tools/new">+ 添加工具</RouterLink>
    </div>

    <section class="search-panel" aria-label="搜索和筛选">
      <input v-model="query" class="search-input" type="search" placeholder="搜索名称、标签、收藏原因或使用场景…" />
      <div class="filter-row">
        <select v-model="category" aria-label="分类">
          <option value="">所有分类</option>
          <option v-for="item in categories" :key="item.id" :value="item.slug">{{ item.name }}</option>
        </select>
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

    <div class="result-meta"><span>{{ loading ? '正在搜索…' : `找到 ${total} 个工具` }}</span></div>
    <ErrorAlert v-if="error" :error="error" />

    <div v-if="!loading && tools.length" class="tool-grid">
      <ToolCard v-for="tool in tools" :key="tool.id" :tool="tool" />
    </div>
    <div v-else-if="!loading" class="empty-state">
      <h2>{{ hasFilters ? '没有匹配的工具' : '你的工具库还是空的' }}</h2>
      <p>{{ hasFilters ? '换个关键词或减少筛选条件试试。' : '从下一个让你眼前一亮的 AI 工具开始。' }}</p>
      <RouterLink v-if="!hasFilters" class="button button-primary" to="/tools/new">记录第一个工具</RouterLink>
    </div>
  </section>
</template>
