<template>
  <el-dialog
    :model-value="modelValue"
    title="任务详情"
    width="70%"
    destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template v-if="task">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="文件名">{{ task.filename }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTag(task.status).type" size="small" effect="light">
            {{ getStatusTag(task.status).label }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ task.created_at }}</el-descriptions-item>
      </el-descriptions>

      <div class="json-section">
        <h4 class="section-title">提取结果</h4>
        <JsonPreview :data="task.extracted_json" />
      </div>
    </template>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { useStatusTag } from '@/composables/useStatusTag'
import JsonPreview from '@/components/common/JsonPreview.vue'

defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  task: {
    type: Object,
    default: null,
  },
})

defineEmits(['update:modelValue'])

const { getStatusTag } = useStatusTag()
</script>

<style scoped>
.json-section {
  margin-top: 20px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
}
</style>
