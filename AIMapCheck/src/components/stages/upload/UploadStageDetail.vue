<template>
  <div class="stage-detail">
    <div class="panel-overlay" @click="$emit('close')"></div>
    <div class="panel-content">
      <div class="panel-header">
        <h3>地图上传</h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="panel-body">
        <div class="status-section">
          <div class="status-badge" :class="currentStatus || stageData?.status || 'pending'">
            {{ getStatusText(currentStatus || stageData?.status || 'pending') }}
          </div>
          <div v-if="stageData?.progress !== undefined" class="progress-bar">
            <div class="progress-fill" :style="{ width: `${stageData.progress}%` }"></div>
            <span class="progress-text">{{ stageData.progress }}%</span>
          </div>
        </div>

        <div class="description-section">
          <p>在此阶段，您需要上传需要进行审查的地图文件。支持的文件格式包括：JPG、PNG、PDF、DWG。上传完成后系统会自动进入参数设置阶段。</p>
        </div>

        <div class="upload-section">
          <input
            ref="fileInput"
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,.dwg"
            style="display: none"
            @change="handleFileChange"
            :disabled="isUploading || isSimulating" 
          />
          <button class="upload-button" @click="triggerFileInput" :disabled="isUploading || isSimulating">
            <i class="fas fa-upload"></i>
            {{ getButtonText() }}
          </button>
          <p class="upload-hint">支持的文件格式：JPG、PNG、PDF、DWG</p>
          
          <div v-if="isUploading || isSimulating" class="upload-progress-bar">
            <div class="upload-progress-fill" :style="{ width: `${currentProgress}%` }"></div>
            <span class="upload-progress-text">{{ currentProgress }}% {{ isUploading ? '(上传中)' : '(处理中)' }}</span>
          </div>
        </div>
        <!-- <button class="upload-button" @click="visualizeMap">
            <i class="fas fa-upload"></i>
            可视化地图
          </button> -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import type { AxiosProgressEvent } from 'axios'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'


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
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'upload-completed'): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const isSimulating = ref(false)
const simulatedProgress = ref(0)
const simulationInterval = ref<number | null>(null)

const statusMap: Record<string, string> = {
  'pending': '待处理',
  'in_progress': '处理中',
  'completed': '已完成',
  'error': '错误'
}

const currentStatus = computed(() => {
  if (isUploading.value || isSimulating.value) return 'in_progress'
  return stageData.value?.status
})

const currentProgress = computed(() => {
  return isUploading.value ? uploadProgress.value : simulatedProgress.value
})

const getStatusText = (status: string | undefined) => {
  if (isUploading.value) return '上传中'
  if (isSimulating.value) return '处理中'
  return statusMap[status || ''] || status || ''
}

const getButtonText = () => {
  if (isUploading.value) return '上传中...'
  if (isSimulating.value) return '处理中...'
  return '选择文件'
}

const stopSimulation = () => {
  if (simulationInterval.value) {
    clearInterval(simulationInterval.value)
    simulationInterval.value = null
  }
  isSimulating.value = false
  simulatedProgress.value = 0
}

const startSimulation = (durationSeconds = 0) => {
  stopSimulation()
  isSimulating.value = true
  simulatedProgress.value = 0
  const steps = 100
  const intervalTime = (durationSeconds * 1000) / steps

  simulationInterval.value = window.setInterval(() => {
    simulatedProgress.value += 1
    if (simulatedProgress.value >= 100) {
      stopSimulation()
      ElMessage.success('地图上传成功')
      emit('upload-completed')
      setTimeout(getStageData, 1000)
    }
  }, intervalTime)
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  
  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)

  stopSimulation()
  isUploading.value = true
  uploadProgress.value = 0

  try {
    await axios.post(
      `http://8.148.68.206:5000/api/tasks/${taskId}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      }
    )
    // console.log("文件传输成功，开始模拟处理进度")
    isUploading.value = false
    startSimulation(3)

  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
    isUploading.value = false
    stopSimulation()
  } finally {
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}

onUnmounted(() => {
  stopSimulation()
})

// const visualizeMap = () => {
//   emit('action-executed')
// } 

</script>

<style scoped>
.stage-detail {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.panel-content {
  position: relative;
  width: 400px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #e0e5f2;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 20px;
  color: #2b3674;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #707eae;
  cursor: pointer;
  padding: 4px;
  
  &:hover {
    color: #2b3674;
  }
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-badge {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  align-self: flex-start;
  
  &.pending {
    background: #f4f7fe;
    color: #a3aed0;
  }
  
  &.in_progress {
    background: #e9f7ff;
    color: #009ef7;
  }
  
  &.completed {
    background: #e6f6f4;
    color: #05cd99;
  }
  
  &.error {
    background: #ffe2e5;
    color: #f1416c;
  }
}

.progress-bar {
  height: 8px;
  background: #f4f7fe;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #4318FF;
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  right: 0;
  top: -20px;
  font-size: 12px;
  color: #707eae;
}

.description-section {
  p {
    margin: 0;
    font-size: 14px;
    color: #2b3674;
    line-height: 1.6;
  }
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 2px dashed #e0e5f2;
  border-radius: 8px;
}

.upload-button {
  background: #4318ff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:hover {
    background: #3311cc;
  }
  
  i {
    font-size: 18px;
  }
}

.upload-button:disabled {
  background: #a3aed0; 
  cursor: not-allowed;
}

.upload-hint {
  margin: 0;
  font-size: 14px;
  color: #a3aed0;
}

.upload-progress-bar {
  width: 100%;
  height: 8px;
  background: #f4f7fe;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  margin-top: 12px; 
}

.upload-progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #4318FF;
  transition: width 0.3s ease;
}

.upload-progress-text {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  color: white;
  z-index: 1;
  mix-blend-mode: difference;
  line-height: 8px;
}
</style> 