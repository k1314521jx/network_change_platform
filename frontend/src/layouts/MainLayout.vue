<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '170px'" class="sidebar">
      <div class="sidebar-brand">
        <el-icon :size="28" color="#409EFF"><Coin /></el-icon>
        <span v-show="!isCollapsed" class="brand-text">网络变更平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
        background-color="#1d1e2c"
        text-color="#a0a3bd"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item index="/module-a">
          <el-icon><Upload /></el-icon>
          <template #title>方案规则化</template>
        </el-menu-item>
        <el-menu-item index="/module-b">
          <el-icon><Cpu /></el-icon>
          <template #title>图谱生成</template>
        </el-menu-item>
        <el-menu-item index="/module-c">
          <el-icon><CircleCheck /></el-icon>
          <template #title>图谱审核</template>
        </el-menu-item>
        <el-menu-item index="/module-d">
          <el-icon><Coin /></el-icon>
          <template #title>图谱入库</template>
        </el-menu-item>
        <el-menu-item index="/module-f">
          <el-icon><Share /></el-icon>
          <template #title>关系图谱</template>
        </el-menu-item>
        <el-menu-item index="/module-e">
          <el-icon><Tools /></el-icon>
          <template #title>配置中心</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top-header">
        <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
        <span class="header-title">网络变更方案智能化处理平台</span>
        <div class="header-right">
          <span class="header-user">{{ username }}</span>
          <el-button link type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { logout } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const activeMenu = computed(() => route.path)
const username = computed(() => localStorage.getItem('username') || '')

async function handleLogout() {
  try { await logout() } catch {}
  localStorage.removeItem('loggedIn')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.sidebar {
  background: #1d1e2c;
  transition: width 0.3s;
  overflow: hidden;
}
.sidebar-brand {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.brand-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}
.top-header {
  display: flex;
  align-items: center;
  height: 60px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.collapse-btn {
  cursor: pointer;
  font-size: 20px;
  margin-right: 16px;
  color: #606266;
}
.collapse-btn:hover {
  color: #409EFF;
}
.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}
.header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-user {
  font-size: 13px;
  color: #606266;
}
.main-content {
  background: #f0f2f5;
  overflow-y: auto;
}
.el-menu {
  border-right: none;
}
</style>
