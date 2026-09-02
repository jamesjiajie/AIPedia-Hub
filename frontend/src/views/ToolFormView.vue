<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'
import ToolForm from '@/components/ToolForm.vue'
import { emptyTool, type CrawlJob, type ToolPayload } from '@/types'

const route = useRoute()
const router = useRouter()
const id = route.params.id as string | undefined
const initialValue = ref<ToolPayload>(emptyTool())
const loading = ref(Boolean(id))
const saving = ref(false)
const error = ref<unknown>(null)
const crawling = ref(false)
const crawlJob = ref<CrawlJob | null>(null)

onMounted(async () => {
  if (!id) return
  try {
    initialValue.value = await api.getTool(id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法读取工具。')
  } finally {
    loading.value = false
  }
})

async function save(payload: ToolPayload): Promise<void> {
  saving.value = true
  error.value = ''
  try {
    const tool = id ? await api.updateTool(id, payload) : await api.createTool(payload)
    await router.push(`/tools/${tool.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('保存失败，请稍后再试。')
  } finally {
    saving.value = false
  }
}

function mergeDraft(current: ToolPayload, draft: ToolPayload): ToolPayload {
  return {
    ...draft,
    official_url: current.official_url || draft.official_url,
    source_url: current.source_url || draft.source_url,
    aliases: current.aliases.length ? current.aliases : draft.aliases,
    tags: current.tags.length ? current.tags : draft.tags,
    platforms: current.platforms.length ? current.platforms : draft.platforms,
    why_saved: current.why_saved,
    notes: current.notes,
    is_favorite: current.is_favorite,
    status: current.status,
  }
}

async function crawl(payload: ToolPayload): Promise<void> {
  error.value = ''
  try {
    crawling.value = true
    crawlJob.value = await api.startCrawl({
      tool_name: payload.name,
      official_url: payload.official_url,
      source_url: payload.source_url,
      user_hint: payload.use_cases,
    })
    while (crawlJob.value && !['completed', 'failed'].includes(crawlJob.value.status)) {
      await new Promise((resolve) => window.setTimeout(resolve, 800))
      crawlJob.value = await api.getCrawl(crawlJob.value.job_id)
    }
    if (crawlJob.value?.status === 'completed' && crawlJob.value.draft) {
      initialValue.value = mergeDraft(payload, crawlJob.value.draft.tool)
    } else if (crawlJob.value?.error) {
      error.value = new Error(crawlJob.value.error)
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法启动抓取任务。')
  } finally {
    crawling.value = false
  }
}
</script>

<template>
  <section class="page narrow-page">
    <RouterLink class="back-link" to="/">← 返回工具库</RouterLink>
    <p class="eyebrow">{{ id ? '维护记录' : '快速收藏' }}</p>
    <h1>{{ id ? '编辑工具' : '记录一个值得记住的工具' }}</h1>
    <p class="subtle">填写官网或发现来源后，可直接抓取页面并让 Agnes 回填草稿；个人收藏原因和备注始终由你保留。</p>
    <p v-if="loading">正在读取记录…</p>
    <ToolForm v-else :initial-value="initialValue" :saving="saving" :crawling="crawling" :crawl-job="crawlJob" :error="error" @submit="save" @crawl="crawl" @cancel="router.back()" />
  </section>
</template>
