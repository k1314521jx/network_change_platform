<template>
  <el-card shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><CircleCheck /></el-icon>
        <span>选择已通过数据</span>
      </div>
    </template>
    <el-scrollbar height="350px">
      <el-checkbox-group v-model="selectedIds">
        <div v-for="item in reviews" :key="item.id" class="check-item">
          <el-checkbox :value="item.id">
            <span class="check-label">#{{ item.triple_task_id }} | {{ item.reviewer || '-' }}</span>
            <div class="check-time">{{ formatDateTime(item.review_time) }}</div>
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <div v-if="!reviews.length" class="empty-tip">暂无已通过数据</div>
    </el-scrollbar>
  </el-card>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getApprovedList } from '@/api/review'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])

const selectedIds = ref([...props.modelValue])
const reviews = ref([])

watch(() => props.modelValue, (val) => { selectedIds.value = val })
watch(selectedIds, (val) => { emit('update:modelValue', val) })

onMounted(async () => {
  try {
    const res = await getApprovedList()
    reviews.value = res.data || []
  } catch {}
})

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.check-item { padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.check-label { font-size: 13px; }
.check-time { font-size: 12px; color: #c0c4cc; }
.empty-tip { text-align: center; color: #c0c4cc; padding: 40px 0; }
</style>
