<template>
  <div class="module-f">
    <div class="module-f-layout">
      <div class="module-f-left">
        <GraphControlPanel
          :labelOptions="labelOptions"
          :relTypeOptions="relTypeOptions"
          :loading="loading"
          @load-graph="handleLoadGraph"
          @find-path="handleFindPath"
          @clear-path="handleClearPath"
          @update:labelColors="labelColors = $event"
          @update:relTypeColors="relTypeColors = $event"
        />
      </div>
      <div class="module-f-right">
        <GraphCanvas
          :graphData="graphData"
          :pathData="pathData"
          :labelColors="labelColors"
          :relTypeColors="relTypeColors"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FullScreen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getGraphLabels, getGraphRelTypes, getGraphData, getShortestPath } from '@/api/graph'
import GraphControlPanel from '@/components/module-f/GraphControlPanel.vue'
import GraphCanvas from '@/components/module-f/GraphCanvas.vue'

const labelOptions = ref([])
const relTypeOptions = ref([])
const graphData = ref(null)
const pathData = ref(null)
const labelColors = ref({})
const relTypeColors = ref({})
const loading = ref(false)

onMounted(async () => {
  try {
    const [lr, rr] = await Promise.all([getGraphLabels(), getGraphRelTypes()])
    labelOptions.value = lr.data || []
    relTypeOptions.value = rr.data || []
  } catch {}
})

async function handleLoadGraph(labels, relTypes) {
  loading.value = true
  pathData.value = null
  try {
    const res = await getGraphData({
      labels: labels.join(','),
      rel_types: relTypes.join(','),
      limit: 500,
    })
    graphData.value = res.data
    const total = (res.data.nodes?.length || 0) + (res.data.edges?.length || 0)
    ElMessage.success(`加载完成: ${res.data.nodes?.length || 0} 个节点, ${res.data.edges?.length || 0} 条关系`)
  } catch {} finally {
    loading.value = false
  }
}

async function handleFindPath(start, end) {
  try {
    const startLabel = start.labels?.[0] || ''
    const endLabel = end.labels?.[0] || ''
    const res = await getShortestPath({
      start_label: startLabel,
      start_id: start.id,
      end_label: endLabel,
      end_id: end.id,
    })
    if (!res.data) {
      ElMessage.warning('未找到路径')
      pathData.value = null
      return
    }
    pathData.value = res.data
    ElMessage.success(`找到路径，长度: ${res.data.length}`)
  } catch {}
}

function handleClearPath() {
  pathData.value = null
}
</script>

<style scoped>
.module-f {
  height: calc(100vh - 120px);
  padding: 12px;
}
.module-f-layout {
  display: flex;
  height: 100%;
  gap: 16px;
}
.module-f-left {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.module-f-right {
  flex: 4;
  min-width: 0;
  position: sticky;
  top: 0;
  height: 100%;
  overflow: hidden;
}
</style>
