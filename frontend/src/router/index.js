import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
      {
        path: 'rule-extract',
        name: 'RuleExtract',
        component: () => import('@/views/ModuleA.vue'),
        meta: { title: '规则提取' },
      },
      {
        path: 'triple-convert',
        name: 'TripleConvert',
        component: () => import('@/views/ModuleB.vue'),
        meta: { title: '三元组转换' },
      },
      {
        path: 'triple-review',
        name: 'TripleReview',
        component: () => import('@/views/ModuleC.vue'),
        meta: { title: '三元组审核' },
      },
      {
        path: 'neo4j-import',
        name: 'Neo4jImport',
        component: () => import('@/views/ModuleD.vue'),
        meta: { title: '图谱入库' },
      },
      {
        path: 'graph-view',
        name: 'GraphView',
        component: () => import('@/views/ModuleF.vue'),
        meta: { title: '图谱可视化' },
      },
      {
        path: 'settings',
        name: 'Settings',
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

  if (to.meta.public) return true

  if (!localStorage.getItem('loggedIn')) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})

export default router
