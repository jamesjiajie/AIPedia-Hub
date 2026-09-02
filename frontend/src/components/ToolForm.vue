<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import ErrorAlert from '@/components/ErrorAlert.vue'
import type { CrawlJob, ToolPayload } from '@/types'

const props = defineProps<{ initialValue: ToolPayload; saving?: boolean; crawling?: boolean; crawlJob?: CrawlJob | null; error?: unknown }>()
const emit = defineEmits<{ submit: [payload: ToolPayload]; crawl: [payload: ToolPayload]; cancel: [] }>()

const form = reactive<ToolPayload>({ ...props.initialValue, aliases: [], tags: [], platforms: [] })
const aliasesInput = ref(props.initialValue.aliases.join(', '))
const tagsInput = ref(props.initialValue.tags.join(', '))
const platformsInput = ref(props.initialValue.platforms.join(', '))

watch(
  () => props.initialValue,
  (value) => {
    Object.assign(form, value)
    aliasesInput.value = value.aliases.join(', ')
    tagsInput.value = value.tags.join(', ')
    platformsInput.value = value.platforms.join(', ')
  },
  { deep: true },
)

const canSubmit = computed(() => Boolean(form.name.trim() && (form.official_url || form.summary || form.why_saved)))

function split(value: string): string[] {
  return [...new Set(value.split(',').map((item) => item.trim()).filter(Boolean))]
}

function submit(): void {
  if (!canSubmit.value) return
  emit('submit', payload())
}

function payload(): ToolPayload {
  return {
    name: form.name.trim(),
    aliases: split(aliasesInput.value),
    tags: split(tagsInput.value),
    platforms: split(platformsInput.value),
    official_url: form.official_url || null,
    source_url: form.source_url || null,
    summary: form.summary || null,
    why_saved: form.why_saved || null,
    use_cases: form.use_cases || null,
    notes: form.notes || null,
    category: form.category || null,
    pricing_model: form.pricing_model,
    is_favorite: form.is_favorite,
    status: form.status,
  }
}

const canCrawl = computed(() => Boolean(form.name.trim() && (form.official_url || form.source_url)))
const draftFields = computed(() => {
  const draft = props.crawlJob?.draft?.tool
  if (!draft) return []
  const values: Array<[string, string]> = [
    ['名称', draft.name],
    ['一句话说明', draft.summary ?? '未生成'],
    ['分类', draft.category ?? '未生成'],
    ['标签', draft.tags.length ? draft.tags.join('、') : '未生成'],
    ['价格模式', draft.pricing_model],
    ['平台', draft.platforms.length ? draft.platforms.join('、') : '未生成'],
    ['使用场景', draft.use_cases ?? '未生成'],
  ]
  return values
})
</script>

<template>
  <form class="tool-form" @submit.prevent="submit">
    <ErrorAlert v-if="error" :error="error" />
    <div class="form-grid">
      <label>
        名称 <span class="required">*</span>
        <input v-model="form.name" required maxlength="255" placeholder="例如 Archify" />
      </label>
      <label>
        官网链接
        <input v-model="form.official_url" type="url" placeholder="https://…" />
      </label>
      <label>
        别名
        <input v-model="aliasesInput" placeholder="用逗号分隔" />
      </label>
      <label>
        分类
        <input v-model="form.category" placeholder="例如：开发工具" />
      </label>
      <label>
        标签
        <input v-model="tagsInput" placeholder="例如：代码库, 架构" />
      </label>
      <label>
        价格模式
        <select v-model="form.pricing_model">
          <option value="unknown">未知</option>
          <option value="free">免费</option>
          <option value="freemium">免费增值</option>
          <option value="paid">付费</option>
          <option value="open_source">开源</option>
        </select>
      </label>
      <label>
        平台
        <input v-model="platformsInput" placeholder="例如：Web, macOS" />
      </label>
      <label>
        发现来源
        <input v-model="form.source_url" type="url" placeholder="文章、视频或帖子链接" />
      </label>
    </div>
    <label>
      一句话说明
      <textarea v-model="form.summary" rows="2" placeholder="这个工具是做什么的？" />
    </label>
    <label>
      我为什么收藏它（可选）
      <textarea v-model="form.why_saved" rows="3" placeholder="当时什么吸引了你？" />
    </label>
    <label>
      什么时候使用
      <textarea v-model="form.use_cases" rows="3" placeholder="下次遇到什么任务时，可以想起它？" />
    </label>
    <label>
      个人备注
      <textarea v-model="form.notes" rows="4" placeholder="补充体验、限制、替代品等" />
    </label>
    <label class="checkbox-row"><input v-model="form.is_favorite" type="checkbox" /> 设为收藏</label>
    <section class="crawl-panel">
      <div><strong>智能抓取与整理</strong><p>GitHub 仓库会优先读取 README 与产品文档；Agnes 先生成研究总结，再回填可审核字段。</p></div>
      <button type="button" class="button button-secondary" :disabled="crawling || !canCrawl" @click="emit('crawl', payload())">
        {{ crawling ? '抓取处理中…' : '抓取并智能回填' }}
      </button>
      <template v-if="crawlJob">
        <div class="crawl-progress" role="progressbar" :aria-valuenow="crawlJob.progress" aria-valuemin="0" aria-valuemax="100"><span :style="{ width: `${crawlJob.progress}%` }" /></div>
        <p class="subtle">{{ crawlJob.message }}（{{ crawlJob.progress }}%）</p>
        <details class="crawl-console" open>
          <summary>抓取控制台（{{ crawlJob.status }}）</summary>
          <ol>
            <li v-for="event in crawlJob.events" :key="`${event.at}-${event.message}`" :class="`console-${event.level}`">
              <time>{{ new Date(event.at).toLocaleTimeString('zh-CN') }}</time> {{ event.message }}
            </li>
          </ol>
        </details>
        <section v-if="crawlJob.status === 'completed' && crawlJob.draft" class="draft-review">
          <p class="eyebrow">审核草稿</p>
          <h3>以下内容已回填到上方表单</h3>
          <p class="subtle">请核对后直接修改表单字段；确认无误再保存工具。</p>
          <dl class="draft-fields">
            <template v-for="[label, value] in draftFields" :key="label"><dt>{{ label }}</dt><dd>{{ value }}</dd></template>
          </dl>
          <details v-if="crawlJob.draft.research_summary" open class="research-summary">
            <summary>项目研究总结（请核对来源后保存）</summary>
            <div>{{ crawlJob.draft.research_summary }}</div>
          </details>
          <details v-if="crawlJob.draft.field_evidence.length" open>
            <summary>字段证据（{{ crawlJob.draft.field_evidence.length }}）</summary>
            <ul><li v-for="item in crawlJob.draft.field_evidence" :key="`${item.field}-${item.source_url}`"><strong>{{ item.field }}</strong>：{{ item.quote || '来源已确认' }}</li></ul>
          </details>
          <p v-if="crawlJob.draft.unsupported_fields.length" class="subtle">尚未确认：{{ crawlJob.draft.unsupported_fields.join('、') }}</p>
        </section>
      </template>
    </section>
    <div class="form-actions">
      <button type="button" class="button button-secondary" @click="emit('cancel')">取消</button>
      <button type="submit" class="button button-primary" :disabled="saving || !canSubmit">
        {{ saving ? '保存中…' : '保存工具' }}
      </button>
    </div>
  </form>
</template>
