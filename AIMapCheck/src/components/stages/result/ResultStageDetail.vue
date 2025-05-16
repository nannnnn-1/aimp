<template>
  <div class="stage-detail">
    <div class="panel-overlay" @click="$emit('close')"></div>
    <div class="panel-content">
      <div class="panel-header">
        <h3>结果预览</h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="panel-body">
        <div class="status-section">
          <div class="status-badge" :class="stageData?.status">
            {{ getStatusText(stageData?.status || '') }}
          </div>
          <div v-if="stageData?.progress !== undefined" class="progress-bar">
            <div class="progress-fill" :style="{ width: `${stageData.progress}%` }"></div>
            <span class="progress-text">{{ stageData.progress }}%</span>
          </div>
        </div>

        <div class="description-section">
          <p>在这个阶段，您可以预览地图分析和审核的最终结果。请仔细检查结果是否符合预期。如果您认为结果无误，请点击"确认结果"按钮完成此阶段。</p>
        </div>

        <div class="actions">
          <el-button 
            type="primary" 
            :loading="loading"
            :disabled="loading || isCompleted"
            @click="handleConfirm"
          >
            {{ isCompleted ? '已确认' : '确认结果' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
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
  const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/5`)
  stageData.value = response.data.stage
}
onMounted(async () => {
  await getStageData()
})
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'result_confirmed'): void
}>()

const loading = ref(false)

const statusMap: Record<string, string> = {
  'pending': '待处理',
  'in_progress': '处理中',
  'completed': '已完成',
  'error': '错误'
}

const getStatusText = (status: string) => {
  return statusMap[status] || status
}

const isCompleted = computed(() => {
  return stageData.value?.status === 'completed'
})

const handleConfirm = async () => {
  if (!taskId) return
  
  try {
    loading.value = true
    await axios.post(
      `http://8.148.68.206:5000/api/tasks/${taskId}/result/confirm`,
      null,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    ElMessage.success('结果已确认！')
    emit('result_confirmed')
  } catch (error: any) {
    console.error('确认结果失败:', error)
    ElMessage.error('确认结果失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}
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
    background: #fff5f8;
    color: #f1416c;
  }
}

.progress-bar {
  background: #f4f7fe;
  height: 8px;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #009ef7;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  right: 8px;
  top: -18px;
  font-size: 12px;
  color: #a3aed0;
}

.description-section {
  color: #2b3674;
  line-height: 1.6;
  
  p {
    margin: 0 0 16px;
  }
}

.actions {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #e0e5f2;
  display: flex;
  justify-content: flex-end;
}
</style> 