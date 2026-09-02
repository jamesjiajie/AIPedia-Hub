<script setup lang="ts">
import { computed, ref } from 'vue'

import { ApiError } from '@/api'

const props = defineProps<{ error: unknown; fallback?: string }>()
const expanded = ref(false)

const message = computed(() => {
  if (props.error instanceof ApiError) return props.error.message
  if (props.error instanceof Error) return props.error.message
  return props.fallback ?? '操作失败，请稍后再试。'
})

const detail = computed(() => {
  if (props.error instanceof ApiError) {
    const status = props.error.status ? `HTTP ${props.error.status}` : '网络连接失败'
    return `${status}\n请求：/api${props.error.path}\n详情：${props.error.detail}`
  }
  return null
})
</script>

<template>
  <section class="form-error" role="alert">
    <span>{{ message }}</span>
    <button v-if="detail" type="button" class="error-details-toggle" :aria-expanded="expanded" @click="expanded = !expanded">
      {{ expanded ? '收起错误详情' : '查看错误详情' }}
    </button>
    <pre v-if="expanded && detail" class="error-details">{{ detail }}</pre>
  </section>
</template>
