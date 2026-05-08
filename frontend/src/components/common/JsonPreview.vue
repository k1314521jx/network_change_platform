<template>
  <div class="json-preview">
    <div class="json-toolbar">
      <el-button size="small" text @click="toggleExpand">
        <el-icon><component :is="expanded ? Fold : Expand" /></el-icon>
        {{ expanded ? '折叠全部' : '展开全部' }}
      </el-button>
      <el-button size="small" text @click="copyJson">
        <el-icon><DocumentCopy /></el-icon>
        {{ copied ? '已复制' : '复制JSON' }}
      </el-button>
    </div>
    <VueJsonPretty
      ref="jsonPrettyRef"
      :data="parsedData"
      :deep="expanded ? Infinity : 2"
      :show-length="true"
      :collapsed-on-click-brackets="true"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'
import { Expand, Fold, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  data: { type: [Object, Array, String, Number, Boolean], default: null },
})

const expanded = ref(false)
const copied = ref(false)
const jsonPrettyRef = ref(null)

const parsedData = computed(() => {
  if (props.data === null || props.data === undefined) return null
  if (typeof props.data === 'object') return props.data
  try {
    return JSON.parse(String(props.data))
  } catch {
    return String(props.data)
  }
})

function toggleExpand() {
  expanded.value = !expanded.value
}

async function copyJson() {
  try {
    const text = JSON.stringify(parsedData.value, null, 2)
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.json-preview {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 16px;
  max-height: 600px;
  overflow-y: auto;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}
.json-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  margin-bottom: 8px;
}
.json-toolbar :deep(.el-button) {
  color: #9399b2;
  font-size: 12px;
}
.json-toolbar :deep(.el-button:hover) {
  color: #cdd6f4;
}
.json-preview :deep(.vjs-tree) {
  color: #cdd6f4;
}
.json-preview :deep(.vjs-key) {
  color: #89b4fa;
}
.json-preview :deep(.vjs-value__string) {
  color: #a6e3a1;
}
.json-preview :deep(.vjs-value__number) {
  color: #fab387;
}
.json-preview :deep(.vjs-value__boolean) {
  color: #cba6f7;
}
.json-preview :deep(.vjs-value__null) {
  color: #f38ba8;
}
.json-preview :deep(.vjs-brackets) {
  color: #9399b2;
}
.json-preview :deep(.vjs-colon) {
  color: #9399b2;
}
.json-preview :deep(.vjs-comment) {
  color: #6c7086;
}
.json-preview :deep(.vjs-tree-node:hover) {
  background: rgba(137, 180, 250, 0.08);
}
</style>
