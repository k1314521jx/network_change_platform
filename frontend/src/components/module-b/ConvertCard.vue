<template>
  <el-card shadow="never" class="action-card">
    <div class="action-bar">
      <el-select v-model="ruleTaskId" placeholder="选择规则化数据" filterable style="width: 340px;">
        <el-option
          v-for="t in ruleTasks"
          :key="t.id"
          :label="`#${t.id} - ${t.filename}`"
          :value="t.id"
        />
      </el-select>
      <el-select v-model="model" placeholder="选择模型" style="width: 160px;">
        <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.name" />
      </el-select>
      <el-select v-model="promptId" placeholder="默认提示词" clearable style="width: 180px;">
        <el-option v-for="p in promptOptions" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" :loading="converting" @click="doConvert">开始转换</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSuccessRuleTasks } from '@/api/rule'
import { convertToTriple } from '@/api/triple'
import { getPromptOptions } from '@/api/prompt'
import { getModelOptions } from '@/api/model'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['converted'])
const ruleTaskId = ref(null)
const model = ref('')
const promptId = ref(null)
const promptOptions = ref([])
const modelOptions = ref([])
const ruleTasks = ref([])
const converting = ref(false)

onMounted(async () => {
  try {
    const res = await getSuccessRuleTasks()
    ruleTasks.value = res.data || []
  } catch {}
  try {
    const res = await getPromptOptions({ type: 'extraction' })
    promptOptions.value = res.data || []
  } catch {}
  try {
    const res = await getModelOptions()
    modelOptions.value = res.data || []
    if (modelOptions.value.length && !model.value) {
      model.value = modelOptions.value[0].name
    }
  } catch {}
})

async function doConvert() {
  if (!ruleTaskId.value) {
    ElMessage.warning('请先选择规则化数据')
    return
  }
  converting.value = true
  try {
    await convertToTriple({ rule_task_id: ruleTaskId.value, model: model.value, prompt_id: promptId.value })
    ElMessage.success('转换任务已创建')
    emit('converted')
  } catch {} finally {
    converting.value = false
  }
}
</script>

<style scoped>
.action-card :deep(.el-card__body) { padding: 12px 16px; }
.action-bar { display: flex; gap: 12px; align-items: center; }
</style>
