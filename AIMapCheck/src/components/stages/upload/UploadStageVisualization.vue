<template>
  <div class="stage-visualization">
    <div v-if="stageData?.status === 'completed'" class="preview-content">
      <div class="map-test-container">
        <MapTiles :taskId="taskId" :fileUrl="getFileUrl()" />
      </div>
    </div>
    <div v-else class="empty-state">
      <i class="fas fa-cloud-upload-alt"></i>
      <p>请上传地图文件</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import MapTiles from '@/components/cesium/MapTiles.vue'
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface StageData {
    status: string
    progress?: number
}
const route = useRoute()
// 获取任务Id
const taskId = parseInt(route.params.id as string)
// 获取任务阶段数据
const stageData = ref<StageData | null>(null)
const getStageData = async () => {
  const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/1`)
  stageData.value = response.data.stage
  
}
onMounted(async () => {
  await getStageData()

})


const getFileUrl = () => {
  return `http://8.148.68.206:5000/api/tasks/files/task_${taskId}/original/original_map.png`
}
defineExpose({
  getStageData
})
</script>

<style scoped>
.map-test-container {
  width: 100%;
  height: 100vh;
}
.stage-visualization {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f7fe;
  border-radius: 8px;
  overflow: hidden;
}

.preview-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.file-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  
  i {
    font-size: 48px;
    color: #4318ff;
  }
}

.file-name {
  font-size: 16px;
  color: #2b3674;
  word-break: break-all;
  text-align: center;
}

.download-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4318ff;
  text-decoration: none;
  font-size: 14px;
  
  &:hover {
    text-decoration: underline;
  }
  
  i {
    font-size: 16px;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #a3aed0;
  
  i {
    font-size: 48px;
  }
  
  p {
    margin: 0;
    font-size: 16px;
  }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f1416c;
  font-size: 14px;
  
  i {
    font-size: 16px;
  }
}
</style> 