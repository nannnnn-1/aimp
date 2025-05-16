<template>
  
  <div class="model-view-container">
    <el-tabs v-model="activeTab" type="border-card" class="model-tabs">
      <el-tab-pane label="基础模型库" name="baseLibrary">
        <BaseModelLibrary v-if="activeTab === 'baseLibrary'" />
      </el-tab-pane>
      <el-tab-pane label="我的模型库" name="myLibrary">
        <ModelLibrary ref="modelLibraryRef" v-if="activeTab === 'myLibrary'" />
      </el-tab-pane>
      <el-tab-pane label="大模型微调" name="fineTune">
        <FineTuneForm v-if="activeTab === 'fineTune'" @fine-tune-submitted="handleFineTuneSubmitted" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { ElTabs, ElTabPane, ElMessage } from 'element-plus';
import ModelLibrary from '@/components/models/ModelLibrary.vue';
import FineTuneForm from '@/components/models/FineTuneForm.vue';
import BaseModelLibrary from '@/components/models/BaseModelLibrary.vue';

// --- State ---
const activeTab = ref('baseLibrary');
const modelLibraryRef = ref<InstanceType<typeof ModelLibrary> | null>(null);

// --- Methods ---
const handleFineTuneSubmitted = async (result: { success: boolean; modelId?: number, message?: string }) => {
  if (result.success && result.modelId) {
    const newModelId = result.modelId;
    ElMessage.success(result.message || '微调任务已提交！');
    activeTab.value = 'myLibrary';

    // 使用 nextTick 或 setTimeout 确保 ModelLibrary 组件已挂载并准备好
    // 最好是结合 await 和 setTimeout
    await new Promise(resolve => setTimeout(resolve, 100)); // 短暂等待 Tab 切换

    if (modelLibraryRef.value) {
        try {
            console.log("View: Refreshing models list...");
            await modelLibraryRef.value.refreshModels(); // 等待列表刷新完成
            console.log("View: Models list refreshed.");

            // 再次等待一小段时间，确保 DOM 更新和列表渲染
            await new Promise(resolve => setTimeout(resolve, 150));

            console.log(`View: Triggering simulation for new model ${newModelId}`);
            modelLibraryRef.value.triggerSimulationForModel(newModelId); // 启动模拟

            console.log(`View: Opening details for new model ${newModelId}`);
            await modelLibraryRef.value.openDetailsForModel(newModelId); // 打开详情面板

        } catch (e) {
            console.error("View: Error during post-submit sequence:", e);
            ElMessage.error("处理提交结果时出错");
        }
    } else {
         console.error("View: modelLibraryRef is not available after tab switch.");
         ElMessage.error("无法访问模型库组件");
    }

  } else {
      ElMessage.error(result.message || '微调任务提交失败');
  }
};
</script>

<style scoped>
.page-header { margin-bottom: 10px; padding-bottom: 15px; border-bottom: 1px solid #e0e5f2;}
.page-header h2 { margin-top: 0; margin-bottom: 5px; color: #2b3674; }
.page-header p { margin-top: 0; font-size: 0.95em; color: #707eae; }
.model-view-container {
  padding: 20px;
  height: calc(100vh - 50px); /* Adjust based on your header height */
  display: flex; flex-direction: column;
}
.model-tabs { flex-grow: 1; display: flex; flex-direction: column; }
:deep(.el-tabs__content) { flex-grow: 1; overflow-y: auto; height: 0; padding: 15px; }
</style>