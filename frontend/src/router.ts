import { createRouter, createWebHistory } from 'vue-router'

import ToolDetailView from '@/views/ToolDetailView.vue'
import DiscoveryView from '@/views/DiscoveryView.vue'
import ToolFormView from '@/views/ToolFormView.vue'
import ToolLibraryView from '@/views/ToolLibraryView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ToolLibraryView, name: 'library' },
    { path: '/quant', component: ToolLibraryView, name: 'quant-library' },
    { path: '/project-management', component: ToolLibraryView, name: 'project-library' },
    { path: '/discover', component: DiscoveryView, name: 'discovery' },
    { path: '/tools/new', component: ToolFormView, name: 'tool-new' },
    { path: '/quant/tools/new', component: ToolFormView, name: 'quant-tool-new' },
    { path: '/project-management/tools/new', component: ToolFormView, name: 'project-tool-new' },
    { path: '/tools/:id', component: ToolDetailView, name: 'tool-detail', props: true },
    { path: '/tools/:id/edit', component: ToolFormView, name: 'tool-edit', props: true },
  ],
})
