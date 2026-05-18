<template>
  <div class="graph-canvas-wrapper" :class="{ fullscreen: isFullscreen }">
    <div class="canvas-toolbar">
      <el-button link @click="toggleFullscreen">
        <el-icon><FullScreen /></el-icon>
      </el-button>
    </div>
    <div ref="containerRef" class="graph-canvas" />
    <!-- 节点详情浮窗 -->
    <div v-if="nodeInfo.visible" class="node-popup" :style="{ left: nodeInfo.x + 'px', top: nodeInfo.y + 'px' }">
      <div class="popup-title">{{ nodeInfo.data.name || nodeInfo.data.id }}</div>
      <div class="popup-labels">
        <el-tag v-for="l in nodeInfo.data.labels" :key="l" size="small" type="info" style="margin-right: 4px;">{{ l }}</el-tag>
      </div>
      <el-descriptions :column="1" border size="small" style="margin-top: 8px; max-height: 200px; overflow-y: auto;">
        <el-descriptions-item v-for="(val, key) in nodeInfo.data.properties" :key="key" :label="key">
          {{ typeof val === 'object' ? JSON.stringify(val) : val }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
    <!-- 空状态 -->
    <div v-if="empty" class="empty-tip">选择标签和关系类型后点击"加载图谱"</div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { FullScreen } from '@element-plus/icons-vue'
import cytoscape from 'cytoscape'

const isFullscreen = ref(false)

const props = defineProps({
  graphData: { type: Object, default: null },
  pathData: { type: Object, default: null },
  labelColors: { type: Object, default: () => ({}) },
  relTypeColors: { type: Object, default: () => ({}) },
})

const containerRef = ref(null)
const empty = ref(true)
let cy = null

const nodeInfo = ref({ visible: false, x: 0, y: 0, data: {} })

onMounted(() => {
  if (!containerRef.value) return
  cy = cytoscape({
    container: containerRef.value,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(name)',
          'text-wrap': 'wrap',
          'text-max-width': '80px',
          'font-size': '11px',
          'background-color': '#409EFF',
          'border-width': 1,
          'border-color': '#fff',
          'width': 30,
          'height': 30,
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 1.5,
          'line-color': '#ccc',
          'target-arrow-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(type)',
          'font-size': '9px',
          'text-rotation': 'autorotate',
          'text-opacity': 0.7,
        },
      },
      {
        selector: '.path-highlight',
        style: {
          'border-width': 3,
          'border-color': '#F56C6C',
          'background-color': '#FDE2E2',
          'z-index': 999,
        },
      },
      {
        selector: 'edge.path-highlight',
        style: {
          'width': 4,
          'line-color': '#F56C6C',
          'target-arrow-color': '#F56C6C',
          'z-index': 999,
        },
      },
    ],
    minZoom: 0.3,
    maxZoom: 3,
  })

  // 节点点击显示详情
  cy.on('tap', 'node', (evt) => {
    const node = evt.target
    const pos = node.renderedPosition()
    nodeInfo.value = {
      visible: true,
      x: pos.x + 10,
      y: pos.y + 10,
      data: {
        id: node.id(),
        labels: node.data('labels') || [],
        name: node.data('name') || '',
        properties: node.data('props') || {},
      },
    }
  })

  cy.on('tap', (evt) => {
    if (evt.target === cy) {
      nodeInfo.value.visible = false
    }
  })
})

onBeforeUnmount(() => {
  if (cy) cy.destroy()
})

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => {
    if (cy) cy.resize().fit(30)
  })
}

// 加载图谱数据
watch(() => props.graphData, (data) => {
  if (!cy || !data) return
  cy.elements().remove()
  nodeInfo.value.visible = false

  if (!data.nodes || !data.nodes.length) {
    empty.value = true
    return
  }
  empty.value = false

  const elements = []
  for (const n of data.nodes) {
    elements.push({
      data: {
        id: n.id,
        name: n.name || n.id,
        labels: n.labels,
        label: n.labels[0] || '',
        props: n.properties || {},
      },
    })
  }
  for (const e of data.edges) {
    elements.push({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
      },
    })
  }
  cy.add(elements)
  applyStyles()
  cy.layout({ name: 'cose', animate: true, animationDuration: 500, padding: 30 }).run()
  cy.fit(30)
}, { deep: true })

// 路径高亮
watch(() => props.pathData, (data) => {
  if (!cy) return
  cy.elements().removeClass('path-highlight')
  if (!data || !data.nodes) return

  // 确保路径节点/边在图中
  for (const n of data.nodes) {
    if (!cy.getElementById(n.id).length) {
      cy.add({
        data: {
          id: n.id,
          name: n.name || n.id,
          labels: n.labels,
          label: n.labels[0] || '',
          props: n.properties || {},
        },
      })
    }
  }
  for (const e of data.edges) {
    if (!cy.getElementById(e.id).length) {
      cy.add({
        data: { id: e.id, source: e.source, target: e.target, type: e.type },
      })
    }
  }

  for (const n of data.nodes) {
    cy.getElementById(n.id).addClass('path-highlight')
  }
  for (const e of data.edges) {
    cy.getElementById(e.id).addClass('path-highlight')
  }
})

// 动态样式：按标签/关系类型着色
function applyStyles() {
  if (!cy) return
  for (const [label, color] of Object.entries(props.labelColors)) {
    cy.style()
      .selector(`node[label="${label}"]`)
      .style('background-color', color)
      .update()
  }
  for (const [type, color] of Object.entries(props.relTypeColors)) {
    cy.style()
      .selector(`edge[type="${type}"]`)
      .style('line-color', color)
      .style('target-arrow-color', color)
      .update()
  }
}

watch(() => [props.labelColors, props.relTypeColors], () => {
  applyStyles()
}, { deep: true })
</script>

<style scoped>
.graph-canvas-wrapper {
  position: relative;
  height: 100%;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.graph-canvas-wrapper.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  border-radius: 0;
  border: none;
}
.canvas-toolbar {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
}
.graph-canvas {
  width: 100%;
  flex: 1;
}
.empty-tip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #909399;
  font-size: 14px;
}
.node-popup {
  position: absolute;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  min-width: 180px;
  max-width: 300px;
}
.popup-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}
.popup-labels {
  margin-bottom: 4px;
}
</style>
