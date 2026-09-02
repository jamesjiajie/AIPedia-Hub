<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { Tool } from '@/types'

defineProps<{ tool: Tool }>()

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric' }).format(new Date(value))
}
</script>

<template>
  <article class="tool-card">
    <div class="tool-card-heading">
      <div>
        <RouterLink :to="`/tools/${tool.id}`" class="tool-name">{{ tool.name }}</RouterLink>
        <p v-if="tool.summary" class="tool-summary">{{ tool.summary }}</p>
      </div>
      <span v-if="tool.is_favorite" class="favorite" aria-label="已收藏">★</span>
    </div>
    <p v-if="tool.why_saved" class="memory-note">{{ tool.why_saved }}</p>
    <div class="tag-row">
      <span v-if="tool.category" class="tag tag-category">{{ tool.category }}</span>
      <span v-for="tag in tool.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <footer>更新于 {{ formatDate(tool.updated_at) }}</footer>
  </article>
</template>
