<template>
  <div class="neo4j-status-bar">
    <div class="status-left">
      <el-icon :size="18"><Connection /></el-icon>
      <span class="status-title">Neo4j 图数据库</span>
      <el-divider direction="vertical" />
      <span class="status-label">连接状态</span>
      <el-tag v-if="connected === true" type="success" size="small" effect="dark">已连接</el-tag>
      <el-tag v-else-if="connected === false" type="danger" size="small" effect="dark">未连接</el-tag>
      <el-tag v-else type="warning" size="small" effect="dark">检测中...</el-tag>
    </div>
    <el-button type="primary" :disabled="!connected" @click="emit('select')">
      <el-icon><FolderOpened /></el-icon>
      选择数据
    </el-button>
  </div>
</template>

<script setup>
defineProps({
  connected: { type: [Boolean, null], default: null },
})
const emit = defineEmits(['select'])
</script>

<style scoped>
.neo4j-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.status-label {
  color: #909399;
  font-size: 13px;
}
</style>
