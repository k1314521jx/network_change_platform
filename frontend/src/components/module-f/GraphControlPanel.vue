<template>
  <div class="control-panel">
    <!-- 标签筛选 -->
    <div class="panel-section">
      <div class="section-label">节点标签</div>
      <el-select v-model="selectedLabels" multiple placeholder="选择标签" size="small" style="width: 100%;">
        <el-option v-for="l in labelOptions" :key="l.label" :label="`${l.label} (${l.count})`" :value="l.label" />
      </el-select>
      <div v-for="label in selectedLabels" :key="label" class="color-row">
        <span class="color-label">{{ label }}</span>
        <el-color-picker v-model="labelColors[label]" size="small" @change="emitColors" />
      </div>
    </div>

    <!-- 关系筛选 -->
    <div class="panel-section">
      <div class="section-label">关系类型</div>
      <el-select v-model="selectedRelTypes" multiple placeholder="选择关系类型" size="small" style="width: 100%;">
        <el-option v-for="t in relTypeOptions" :key="t.type" :label="`${t.type} (${t.count})`" :value="t.type" />
      </el-select>
      <div v-for="rt in selectedRelTypes" :key="rt" class="color-row">
        <span class="color-label">{{ rt }}</span>
        <el-color-picker v-model="relTypeColors[rt]" size="small" @change="emitColors" />
      </div>
    </div>

    <!-- 加载按钮 -->
    <div class="panel-section">
      <el-button type="primary" size="small" :loading="loading" :disabled="!selectedLabels.length" style="width: 100%;" @click="handleLoad">
        加载图谱
      </el-button>
    </div>

    <el-divider />

    <!-- 路径查找 -->
    <div class="panel-section">
      <div class="section-label">路径查找</div>
      <el-select
        v-model="startNode"
        filterable
        remote
        reserve-keyword
        placeholder="起始节点"
        :remote-method="searchStart"
        :loading="searchLoading"
        size="small"
        style="width: 100%; margin-bottom: 8px;"
        value-key="id"
      >
        <el-option v-for="n in startOptions" :key="`${n.labels?.[0]}:${n.id}`" :label="`${n.labels?.[0] || ''}: ${n.name || n.id}`" :value="n" />
      </el-select>
      <el-select
        v-model="endNode"
        filterable
        remote
        reserve-keyword
        placeholder="目标节点"
        :remote-method="searchEnd"
        :loading="searchLoading"
        size="small"
        style="width: 100%; margin-bottom: 8px;"
        value-key="id"
      >
        <el-option v-for="n in endOptions" :key="`${n.labels?.[0]}:${n.id}`" :label="`${n.labels?.[0] || ''}: ${n.name || n.id}`" :value="n" />
      </el-select>
      <div style="display: flex; gap: 8px;">
        <el-button type="success" size="small" :disabled="!startNode || !endNode" @click="handleFindPath">查找路径</el-button>
        <el-button size="small" @click="handleClearPath">清除路径</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchNodes } from '@/api/graph'

const DEFAULT_COLORS = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#9B59B6', '#909399', '#FF6B6B', '#4ECDC4']

const props = defineProps({
  labelOptions: { type: Array, default: () => [] },
  relTypeOptions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['load-graph', 'find-path', 'clear-path', 'update:labelColors', 'update:relTypeColors'])

const selectedLabels = ref([])
const selectedRelTypes = ref([])
const labelColors = ref({})
const relTypeColors = ref({})

const startNode = ref(null)
const endNode = ref(null)
const startOptions = ref([])
const endOptions = ref([])
const searchLoading = ref(false)

// 自动分配默认颜色
watch(selectedLabels, (labels) => {
  const colors = { ...labelColors.value }
  labels.forEach((l, i) => {
    if (!colors[l]) colors[l] = DEFAULT_COLORS[i % DEFAULT_COLORS.length]
  })
  labelColors.value = colors
  emitColors()
})

watch(selectedRelTypes, (types) => {
  const colors = { ...relTypeColors.value }
  types.forEach((t, i) => {
    if (!colors[t]) colors[t] = DEFAULT_COLORS[i % DEFAULT_COLORS.length]
  })
  relTypeColors.value = colors
  emitColors()
})

function emitColors() {
  emit('update:labelColors', { ...labelColors.value })
  emit('update:relTypeColors', { ...relTypeColors.value })
}

function handleLoad() {
  emit('load-graph', selectedLabels.value, selectedRelTypes.value)
}

function handleFindPath() {
  if (!startNode.value || !endNode.value) return
  emit('find-path', startNode.value, endNode.value)
}

function handleClearPath() {
  startNode.value = null
  endNode.value = null
  emit('clear-path')
}

async function searchStart(query) {
  if (!query) return
  searchLoading.value = true
  try {
    const res = await searchNodes({ keyword: query, limit: 20 })
    startOptions.value = res.data || []
  } catch {} finally {
    searchLoading.value = false
  }
}

async function searchEnd(query) {
  if (!query) return
  searchLoading.value = true
  try {
    const res = await searchNodes({ keyword: query, limit: 20 })
    endOptions.value = res.data || []
  } catch {} finally {
    searchLoading.value = false
  }
}
</script>

<style scoped>
.control-panel {
  padding: 12px;
  height: 100%;
  overflow-y: auto;
}
.panel-section {
  margin-bottom: 16px;
}
.section-label {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  margin-bottom: 8px;
}
.color-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}
.color-label {
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}
</style>
