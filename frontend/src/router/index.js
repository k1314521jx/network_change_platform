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
        path: 'module-f',
        name: 'ModuleF',
        component: () => import('@/views/ModuleF.vue'),
        meta: { title: '关系图谱查看' },
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

  if (to.meta.public) return true

  if (!localStorage.getItem('loggedIn')) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})

export default router
