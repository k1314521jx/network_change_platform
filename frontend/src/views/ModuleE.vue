<template>
  <div class="module-e">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="抽取提示词" name="extraction">
        <PromptTab type="extraction" />
      </el-tab-pane>
      <el-tab-pane label="审核提示词" name="review">
        <PromptTab type="review" />
      </el-tab-pane>
      <el-tab-pane label="模型配置" name="model">
        <ModelTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PromptTab from '@/components/module-e/PromptTab.vue'
import ModelTab from '@/components/module-e/ModelTab.vue'

const activeTab = ref('extraction')
</script>

<style scoped>
.module-e {
  padding: 4px;
}
</style>
