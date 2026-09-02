<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/api'
import ErrorAlert from '@/components/ErrorAlert.vue'
import ToolForm from '@/components/ToolForm.vue'
import { emptyTool, type ToolDraft, type ToolPayload } from '@/types'

const router = useRouter()
const form = reactive({ toolName: '', sourceUrl: '', sourceTitle: '', sourceType: 'official', excerpt: '', hint: '' })
const drafting = ref(false)
const saving = ref(false)
const error = ref<unknown>(null)
const draft = ref<ToolDraft | null>(null)

async function createDraft(): Promise<void> {
  if (!form.toolName.trim() || !form.sourceUrl.trim() || !form.excerpt.trim()) return
  drafting.value = true
  error.value = ''
  try {
    draft.value = await api.buildToolDraft({
      tool_name: form.toolName.trim(),
      user_hint: form.hint.trim() || null,
      sources: [{
        url: form.sourceUrl.trim(),
        title: form.sourceTitle.trim() || null,
        source_type: form.sourceType,
        excerpt: form.excerpt.trim(),
      }],
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('无法生成草稿，请稍后再试。')
  } finally {
    drafting.value = false
  }
}

async function save(payload: ToolPayload): Promise<void> {
  saving.value = true
  error.value = ''
  try {
    const tool = await api.createTool(payload)
    await router.push(`/tools/${tool.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error('保存失败，请稍后再试。')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="page narrow-page">
    <RouterLink class="back-link" to="/">← 返回工具库</RouterLink>
    <p class="eyebrow">Agnes 智能整理</p>
    <h1>从可信证据生成工具卡</h1>
    <p class="subtle">粘贴官网、文档或 GitHub 的相关摘要。Agnes 只会基于这些证据生成草稿，保存前由你审核。</p>

    <form v-if="!draft" class="tool-form" @submit.prevent="createDraft">
      <ErrorAlert v-if="error" :error="error" />
      <div class="form-grid">
        <label>工具名称 <span class="required">*</span><input v-model="form.toolName" required maxlength="255" placeholder="例如 Archify" /></label>
        <label>证据链接 <span class="required">*</span><input v-model="form.sourceUrl" required type="url" placeholder="https://…" /></label>
        <label>页面标题<input v-model="form.sourceTitle" maxlength="500" placeholder="例如产品首页" /></label>
        <label>来源类型
          <select v-model="form.sourceType"><option value="official">官网</option><option value="documentation">文档</option><option value="github">GitHub</option><option value="article">文章</option></select>
        </label>
      </div>
      <label>页面摘要或证据原文 <span class="required">*</span><textarea v-model="form.excerpt" required rows="10" maxlength="12000" placeholder="粘贴与该工具有关的产品说明、功能、价格或平台信息。" /></label>
      <label>补充提示（可选）<textarea v-model="form.hint" rows="2" maxlength="2000" placeholder="例如：我想重点了解它是否适合代码架构分析。" /></label>
      <div class="form-actions"><button type="button" class="button button-secondary" @click="router.back()">取消</button><button class="button button-primary" :disabled="drafting">{{ drafting ? 'Agnes 整理中…' : '生成可审核草稿' }}</button></div>
    </form>

    <template v-else>
      <p class="form-error">请检查以下草稿；没有证据支持的字段已保留为未知或空值。</p>
      <details v-if="draft.field_evidence.length" open class="detail-section">
        <summary>查看 {{ draft.field_evidence.length }} 条字段证据</summary>
        <ul><li v-for="item in draft.field_evidence" :key="`${item.field}-${item.source_url}`"><strong>{{ item.field }}</strong>：{{ item.quote || '来源已确认' }}</li></ul>
      </details>
      <ToolForm :initial-value="draft.tool || emptyTool()" :saving="saving" :error="error" @submit="save" @cancel="draft = null" />
    </template>
  </section>
</template>
