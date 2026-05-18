<template>
  <div class="module-a">
    <UploadCard @uploaded="onUploaded" />
    <TaskTable ref="taskTable" @view-detail="viewDetail" />
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
