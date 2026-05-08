import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/module-a',
    children: [
      {
        path: 'module-a',
        name: 'ModuleA',
        component: () => import('@/views/ModuleA.vue'),
        meta: { title: '模块A: 历史变更方案规则化' },
      },
      {
        path: 'module-b',
        name: 'ModuleB',
        component: () => import('@/views/ModuleB.vue'),
        meta: { title: '模块B: 规则化转三元组' },
      },
      {
        path: 'module-c',
        name: 'ModuleC',
        component: () => import('@/views/ModuleC.vue'),
        meta: { title: '模块C: 三元组审核' },
      },
      {
        path: 'module-d',
        name: 'ModuleD',
        component: () => import('@/views/ModuleD.vue'),
        meta: { title: '模块D: 三元组入库' },
      },
      {
        path: 'module-e',
        name: 'ModuleE',
        component: () => import('@/views/ModuleE.vue'),
        meta: { title: '配置中心' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = to.meta.title || '网络变更方案智能化处理平台'
})

export default router
