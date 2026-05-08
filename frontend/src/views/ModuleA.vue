<template>
  <div class="module-a">
    <el-row :gutter="20">
      <el-col :span="8">
        <UploadCard @uploaded="onUploaded" />
      </el-col>
      <el-col :span="16">
        <TaskTable ref="taskTable" @view-detail="viewDetail" />
      </el-col>
    </el-row>
    <TaskDetailDialog v-model="detailVisible" :task="currentTask" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UploadCard from '@/components/module-a/UploadCard.vue'
import TaskTable from '@/components/module-a/TaskTable.vue'
import TaskDetailDialog from '@/components/module-a/TaskDetailDialog.vue'

const taskTable = ref(null)
const detailVisible = ref(false)
const currentTask = ref(null)

function onUploaded() {
  taskTable.value?.refresh()
}

async function viewDetail(taskId) {
  const { getRuleTask } = await import('@/api/rule')
  const res = await getRuleTask(taskId)
  currentTask.value = res.data
  detailVisible.value = true
}
</script>

<style scoped>
.module-a {
  padding: 4px;
}
</style>
