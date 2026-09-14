<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { TaxonomyItem, Tool } from '@/types'

const props = defineProps<{ tool: Tool; categories: TaxonomyItem[]; tags: TaxonomyItem[]; moving?: boolean }>()
const emit = defineEmits<{ assign: [target: { type: 'category' | 'tag'; name: string } | null] }>()

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}

function officialDomain(value: string | null): string {
  if (!value) return '官网待补充'
  try {
    return new URL(value).host.replace(/^www\./, '')
  } catch {
    return value
  }
}

function selectedDirectory(): string {
  if (props.tool.category) return `category:${props.tool.category}`
  const matchingTag = props.tags.find((item) => props.tool.tags.includes(item.name))
  return matchingTag ? `tag:${matchingTag.name}` : ''
}

function assign(value: string): void {
  if (!value) return emit('assign', null)
  const [type, ...name] = value.split(':')
  emit('assign', { type: type as 'category' | 'tag', name: name.join(':') })
}
</script>

<template>
  <article class="tool-card">
    <div class="tool-card-main">
      <div class="tool-card-heading">
        <RouterLink :to="`/tools/${tool.id}`" class="tool-name">{{ tool.name }}</RouterLink>
        <span v-if="tool.is_favorite" class="favorite" aria-label="已收藏">★</span>
      </div>
      <a v-if="tool.official_url" class="tool-domain" :href="tool.official_url" target="_blank" rel="noreferrer">{{ officialDomain(tool.official_url) }} ↗</a>
      <p v-else class="tool-domain">{{ officialDomain(tool.official_url) }}</p>
    </div>
    <p v-if="tool.summary" class="tool-summary">{{ tool.summary }}</p>
    <div class="tag-row">
      <span v-if="tool.category" class="tag tag-category">{{ tool.category }}</span>
      <span v-for="tag in tool.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <footer>
      <span>更新于 {{ formatDate(tool.updated_at) }}</span>
      <details class="tool-actions">
        <summary>整理</summary>
        <label class="move-category">
          <span>归入目录</span>
          <select :value="selectedDirectory()" :disabled="moving" @change="assign(($event.target as HTMLSelectElement).value)">
            <option value="">未分类</option>
            <optgroup v-if="tags.length" label="标签目录"><option v-for="item in tags" :key="`tag-${item.id}`" :value="`tag:${item.name}`">{{ item.name }}</option></optgroup>
            <optgroup v-if="categories.length" label="手动分类"><option v-for="item in categories" :key="`category-${item.id}`" :value="`category:${item.name}`">{{ item.name }}</option></optgroup>
          </select>
        </label>
      </details>
    </footer>
  </article>
</template>
