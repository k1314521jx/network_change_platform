<template>
  <el-card shadow="hover" class="upload-card">
    <template #header>
      <div class="card-header">
        <el-icon :size="22" color="#409eff"><UploadFilled /></el-icon>
        <span class="card-title">规则文件上传</span>
      </div>
    </template>

    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :auto-upload="false"
      accept=".xlsx,.xls"
      :limit="1"
      :on-change="onFileChange"
      :on-exceed="onExceed"
      :on-remove="onRemove"
    >
      <div class="upload-content">
        <el-icon :size="48" color="#c0c4cc"><UploadFilled /></el-icon>
        <div class="upload-text">将 Excel 文件拖到此处</div>
        <div class="upload-hint">或 <em>点击上传</em></div>
        <div class="upload-tip">仅支持 .xlsx / .xls 格式</div>
      </div>
    </el-upload>

    <el-progress
      v-if="uploading"
      :percentage="uploadProgress"
      :stroke-width="6"
      :format="progressFormat"
      class="upload-progress"
    />

    <el-button
      type="primary"
      :loading="uploading"
      :disabled="!selectedFile"
      class="upload-btn"
      @click="submitUpload"
    >
      {{ uploading ? '上传中...' : '开始上传' }}
    </el-button>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadExcel } from '@/api/rule'

const emit = defineEmits(['uploaded'])

const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)

function onFileChange(uploadFile) {
  const raw = uploadFile.raw
  const validTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
  ]
  const isExcel = validTypes.includes(raw.type) || raw.name.endsWith('.xlsx') || raw.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error('仅支持 Excel 文件（.xlsx / .xls）')
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    return
  }
  selectedFile.value = raw
}

function onExceed() {
  ElMessage.warning('一次只能上传一个文件，请先移除已有文件')
}

function onRemove() {
  selectedFile.value = null
}

function progressFormat(percentage) {
  return percentage === 100 ? '完成' : `${percentage}%`
}

async function submitUpload() {
  if (!selectedFile.value) return

  uploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    // 模拟上传进度
    const progressTimer = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    await uploadExcel(formData)

    clearInterval(progressTimer)
    uploadProgress.value = 100

    ElMessage.success('文件上传成功')
    emit('uploaded')

    // 重置状态
    setTimeout(() => {
      uploading.value = false
      uploadProgress.value = 0
      selectedFile.value = null
      uploadRef.value?.clearFiles()
    }, 800)
  } catch (e) {
    uploading.value = false
    uploadProgress.value = 0
  }
}
</script>

<style scoped>
.upload-card {
  min-height: 400px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.upload-area {
  width: 100%;
}
.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 30px 0;
}
.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.upload-text {
  font-size: 14px;
  color: #606266;
  margin-top: 8px;
}
.upload-hint {
  font-size: 14px;
  color: #606266;
}
.upload-hint em {
  color: #409eff;
  font-style: normal;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.upload-progress {
  margin-top: 16px;
}
.upload-btn {
  width: 100%;
  margin-top: 16px;
}
</style>
