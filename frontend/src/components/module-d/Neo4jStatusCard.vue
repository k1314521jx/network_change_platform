<template>
  <el-card shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><Connection /></el-icon>
        <span>Neo4j 入库</span>
      </div>
    </template>
    <div class="status-row">
      <span class="status-label">连接状态：</span>
      <el-tag v-if="connected === true" type="success" size="small">已连接</el-tag>
      <el-tag v-else-if="connected === false" type="danger" size="small">未连接</el-tag>
      <el-tag v-else type="warning" size="small">检测中...</el-tag>
    </div>
    <el-button
      type="primary"
      :loading="importing"
      :disabled="!connected || !selectedIds.length"
      @click="emit('import')"
      style="width: 100%; margin-top: 16px;"
    >
      <el-icon><Promotion /></el-icon>
      批量入库 ({{ selectedIds.length }})
    </el-button>
  </el-card>
</template>

<script setup>
defineProps({
  connected: { type: [Boolean, null], default: null },
  selectedIds: { type: Array, default: () => [] },
  importing: { type: Boolean, default: false },
})
const emit = defineEmits(['import'])
</script>

<style scoped>
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.status-row { display: flex; align-items: center; }
.status-label { color: #606266; }
</style>
