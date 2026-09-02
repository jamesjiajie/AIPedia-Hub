<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">A</span>
        <span>AIpedia Hub</span>
      </RouterLink>
      <nav aria-label="主导航">
        <RouterLink to="/">工具库</RouterLink>
        <RouterLink class="button button-primary" to="/tools/new">添加工具</RouterLink>
      </nav>
    </header>
    <RouterView />
  </main>
</template>
