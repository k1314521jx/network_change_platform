<template>
  <div class="module-b">
    <ConvertCard @converted="onConverted" />
    <TripleTaskTable ref="taskTable" @view-detail="viewDetail" style="margin-top: 12px;" />
    <TripleDetailDialog v-model="detailVisible" :task="currentTask" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ConvertCard from '@/components/module-b/ConvertCard.vue'
import TripleTaskTable from '@/components/module-b/TripleTaskTable.vue'
import TripleDetailDialog from '@/components/module-b/TripleDetailDialog.vue'
import { getTripleTask } from '@/api/triple'

const taskTable = ref(null)
const detailVisible = ref(false)
const currentTask = ref(null)

function onConverted() {
  taskTable.value?.refresh()
}

async function viewDetail(taskId) {
  const res = await getTripleTask(taskId)
  currentTask.value = res.data
  detailVisible.value = true
}
</script>

<style scoped>
.module-b { padding: 4px; }
</style>
