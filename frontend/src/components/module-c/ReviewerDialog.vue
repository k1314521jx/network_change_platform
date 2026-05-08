<template>
  <el-dialog v-model="visible" title="确认审核" width="400px" destroy-on-close>
    <el-form>
      <el-form-item label="审核人">
        <el-input v-model="reviewer" placeholder="请输入审核人姓名" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="onConfirm" :disabled="!reviewer.trim()">确认提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const reviewer = ref('')

function onConfirm() {
  if (!reviewer.value.trim()) return
  emit('confirm', reviewer.value.trim())
  reviewer.value = ''
  visible.value = false
}
</script>
