<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

import { api } from '@/api'
import ErrorAlert from '@/components/ErrorAlert.vue'
import type { Tool } from '@/types'

type Message = { role: 'user' | 'assistant'; content: string; tools?: Tool[] }

const props = defineProps<{ scopeTag: string | null }>()
const open = ref(false)
const question = ref('')
const messages = ref<Message[]>([])
const busy = ref(false)
const includePersonalNotes = ref(false)
const error = ref<unknown>(null)
const input = ref<HTMLTextAreaElement | null>(null)
const transcript = ref<HTMLElement | null>(null)

function storageKey(): string {
  return `aipedia-assistant:${props.scopeTag ?? 'all'}`
}

function restore(): void {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    messages.value = Array.isArray(saved) ? saved.filter((item): item is Message =>
      item && (item.role === 'user' || item.role === 'assistant') && typeof item.content === 'string',
    ).slice(-30) : []
  } catch {
    messages.value = []
  }
}

watch(() => props.scopeTag, restore, { immediate: true })

function save(): void {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(messages.value.slice(-30)))
  } catch {
    // The current conversation still works if browser storage is unavailable.
  }
}

async function show(): Promise<void> {
  open.value = true
  await nextTick()
  input.value?.focus()
}

function clear(): void {
  messages.value = []
  error.value = null
  try {
    localStorage.removeItem(storageKey())
  } catch {
    // Browser storage may be unavailable.
  }
  input.value?.focus()
}

async function ask(): Promise<void> {
  const text = question.value.trim()
  if (!text || busy.value) return
  const history = messages.value.slice(-12).map(({ role, content }) => ({ role, content }))
  busy.value = true
  error.value = null
  messages.value.push({ role: 'user', content: text })
  question.value = ''
  try {
    const reply = await api.askAssistant({ question: text, scope_tag: props.scopeTag, include_personal_notes: includePersonalNotes.value, history })
    messages.value.push({ role: 'assistant', content: reply.answer, tools: reply.tools })
    save()
  } catch (reason) {
    messages.value.pop()
    question.value = text
    error.value = reason
  } finally {
    busy.value = false
    await nextTick()
    transcript.value?.scrollTo({ top: transcript.value.scrollHeight, behavior: 'smooth' })
    input.value?.focus()
  }
}
</script>

<template>
  <button class="button button-secondary assistant-trigger" type="button" @click="show">✦ 问 AI 助手</button>
  <Teleport to="body">
    <aside v-if="open" class="assistant-drawer" aria-label="工具库 AI 助手" @keydown.esc="open = false">
      <header class="assistant-header">
        <div><span class="eyebrow">工具库 AI 助手</span><h2>问问你的工具库</h2></div>
        <button class="assistant-close" type="button" aria-label="关闭助手" @click="open = false">×</button>
      </header>
      <div class="assistant-scope">当前范围：{{ scopeTag || '全部活跃工具' }} · 回答基于已保存的记录</div>
      <div ref="transcript" class="assistant-transcript" aria-live="polite">
        <div v-if="!messages.length" class="assistant-welcome">
          <p>描述你要完成的事，我会从工具库里找合适的工具并说明理由。</p>
          <button type="button" @click="question = '有哪些适合做演示文稿的工具？'; input?.focus()">有哪些适合做演示文稿的工具？</button>
          <button type="button" @click="question = '有哪些免费的工具值得试试？'; input?.focus()">有哪些免费的工具值得试试？</button>
        </div>
        <div v-for="(message, index) in messages" :key="index" class="assistant-message" :class="`assistant-${message.role}`">
          <span class="assistant-role">{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
          <p>{{ message.content }}</p>
          <div v-if="message.tools?.length" class="assistant-results">
            <RouterLink v-for="tool in message.tools" :key="tool.id" :to="`/tools/${tool.id}`" @click="open = false">
              <strong>{{ tool.name }}</strong><span>{{ tool.summary || '查看工具详情' }}</span>
            </RouterLink>
          </div>
        </div>
        <p v-if="busy" class="assistant-thinking" role="status">正在查找并整理工具…</p>
      </div>
      <form class="assistant-compose" @submit.prevent="ask">
        <ErrorAlert v-if="error" :error="error" />
        <p class="assistant-privacy">提问会将当前范围的工具名称、摘要、用途、分类等资料发给 Agnes。</p>
        <label class="assistant-personal"><input v-model="includePersonalNotes" type="checkbox" /> 同时使用收藏理由与个人备注</label>
        <label for="assistant-question">继续提问</label>
        <textarea id="assistant-question" ref="input" v-model="question" rows="3" maxlength="2000" placeholder="例如：帮我比较库里适合写代码的工具" @keydown.enter.exact.prevent="ask" />
        <div><button class="text-button" type="button" :disabled="busy || !messages.length" @click="clear">清空对话</button><button class="button button-primary" type="submit" :disabled="busy || !question.trim()">{{ busy ? '回答中…' : '发送' }}</button></div>
      </form>
    </aside>
  </Teleport>
</template>
