<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api } from '@/api'
import ErrorAlert from '@/components/ErrorAlert.vue'
import type { Tool } from '@/types'

const route = useRoute()
const tool = ref<Tool | null>(null)
const error = ref<unknown>(null)
const busy = ref(false)

function formatDate(value: string | null): string {
  if (!value) return '尚未查看'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

onMounted(async () => {
  try {
    tool.value = await api.getTool(String(route.params.id))
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法读取工具。')
  }
})

async function changeStatus(): Promise<void> {
  if (!tool.value) return
  busy.value = true
  try {
    tool.value = tool.value.status === 'archived' ? await api.restoreTool(tool.value.id) : await api.archiveTool(tool.value.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('操作失败。')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="page narrow-page">
    <RouterLink class="back-link" to="/">← 返回工具库</RouterLink>
    <ErrorAlert v-if="error" :error="error" />
    <p v-else-if="!tool">正在读取记录…</p>
    <template v-else>
      <div class="detail-heading">
        <div>
          <div class="title-row"><h1>{{ tool.name }}</h1><span v-if="tool.is_favorite" class="favorite">★</span></div>
          <p v-if="tool.summary" class="subtle detail-summary">{{ tool.summary }}</p>
        </div>
        <div class="detail-actions">
          <a v-if="tool.official_url" class="button button-secondary" :href="tool.official_url" target="_blank" rel="noreferrer">访问官网 ↗</a>
          <RouterLink class="button button-primary" :to="`/tools/${tool.id}/edit`">编辑</RouterLink>
        </div>
      </div>

      <div class="tag-row detail-tags">
        <span v-if="tool.category" class="tag tag-category">{{ tool.category }}</span>
        <span v-for="tag in tool.tags" :key="tag" class="tag">{{ tag }}</span>
        <span class="tag">{{ tool.pricing_model }}</span>
        <span v-if="tool.status !== 'active'" class="tag tag-status">{{ tool.status }}</span>
      </div>

      <section class="detail-section emphasis"><h2>我为什么收藏它</h2><p>{{ tool.why_saved || '尚未记录。' }}</p></section>
      <section class="detail-section"><h2>什么时候使用</h2><p>{{ tool.use_cases || '尚未记录。' }}</p></section>
      <section v-if="tool.notes" class="detail-section"><h2>个人备注</h2><p>{{ tool.notes }}</p></section>
      <section v-if="tool.platforms.length" class="detail-section"><h2>平台</h2><p>{{ tool.platforms.join(' · ') }}</p></section>
      <section class="detail-section metadata">
        <h2>记录信息</h2>
        <p>创建于 {{ formatDate(tool.created_at) }} · 最后查看 {{ formatDate(tool.last_viewed_at) }}</p>
        <a v-if="tool.source_url" :href="tool.source_url" target="_blank" rel="noreferrer">查看发现来源 ↗</a>
      </section>
      <button class="text-button danger-button" type="button" :disabled="busy" @click="changeStatus">
        {{ tool.status === 'archived' ? '恢复工具' : '归档工具' }}
      </button>
    </template>
  </section>
</template>
