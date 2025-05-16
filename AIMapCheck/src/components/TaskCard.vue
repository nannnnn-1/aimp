<template>
  <div class="task-card" @click="navigateToTask" :class="{ 'status-completed': task.status === 'completed' }">
    <div class="task-info">
      <h3>{{ task.name }}</h3>
      <div class="task-meta">
        <span class="task-date">{{ formatDate(task.createTime) }}</span>
        <span class="task-status" :class="task.status">
          {{ getStatusText(task.status) }}
        </span>
      </div>
    </div>
    <div class="task-actions">
      <button class="action-btn monitor" @click.stop="navigateToTask">
        <i class="fas fa-chart-line"></i>
        任务监测
      </button>
      <button 
        class="action-btn report" 
        @click.stop="navigateToReport"
      >
        <i class="fas fa-file-alt"></i>
        查看报告
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

interface Task {
  id: number
  name: string
  status: string
  createTime: string
  hasReport: boolean
}

const props = defineProps<{
  task: Task
}>()
const router = useRouter()

const formatDate = (dateString: string) => {
  try {
    // 解析 ISO 格式的日期字符串
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      console.error('Invalid date:', dateString)
      return '无效日期'
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}`
  } catch (error) {
    console.error('Date formatting error:', error)
    return '日期格式错误'
  }
}

const getStatusText = (status: string) => {
  const statusMap: { [key: string]: string } = {
    'pending': '待处理',
    'in_progress': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

const navigateToTask = () => {
  router.push(`/task/${props.task.id}`)
}

const navigateToReport = () => {
    router.push(`/task/${props.task.id}/report`)
}
</script>

<style scoped>
.task-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
}

.task-info {
  margin-bottom: 16px;
}

.task-info h3 {
  font-size: 18px;
  color: #2b3674;
  margin-bottom: 8px;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-date {
  color: #707eae;
  font-size: 14px;
}

.task-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  
  &.pending {
    background: #f4f7fe;
    color: #a3aed0;
  }
  
  &.in_progress {
    background: #fff6e5;
    color: #ffb547;
  }
  
  &.completed {
    background: #e6f6f4;
    color: #2cd9c5;
  }
  
  &.failed {
    background: #ffe4e4;
    color: #ff3b3b;
  }
}

.task-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
  
  &.monitor {
    background: #4318FF;
    color: white;
    
    &:hover {
      background: #3311cc;
    }
  }
  
  &.report {
    background: #f4f7fe;
    color: #2b3674;
    
    &:hover:not(:disabled) {
      background: #e0e5f2;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}
</style> 