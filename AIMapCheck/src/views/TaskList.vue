<template>
    <div class="task-list">
      <div class="task-header">
        <h2>任务中心</h2>
        <div class="task-actions">
          <button class="btn-add" @click="showCreateDialog = true">
            <i class="fas fa-plus"></i>
            新建任务
          </button>
        </div>
      </div>
  
      <div v-if="loading" class="loading">
        加载中...
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else class="task-grid">
        <TaskCard
          v-for="task in displayedTasks"
          :key="task.id"
          :task="task"
          class="task-card-wrapper"
        />
      </div>
  
      <div class="pagination">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <i class="fas fa-chevron-left"></i>
        </button>
        
        <div class="page-numbers">
          <button 
            v-for="page in totalPages" 
            :key="page"
            class="page-number"
            :class="{ active: page === currentPage }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>
  
        <button 
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          <i class="fas fa-chevron-right"></i>
        </button>
  
        <select v-model="pageSize" class="page-size">
          <option value="10">10条/页</option>
          <option value="20">20条/页</option>
        </select>
      </div>
  
      <CreateTaskDialog
        v-model="showCreateDialog"
        @create="handleCreateTask"
      />
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import TaskCard from '../components/TaskCard.vue'
  import CreateTaskDialog from '../components/CreateTaskDialog.vue'
  
  interface Task {
    id: number
    name: string
    status: string
    createTime: Date
    hasReport: boolean
  }
  
  const router = useRouter()
  const tasks = ref<Task[]>([])
  const loading = ref(true)
  const error = ref('')
  const showCreateDialog = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(10)
  
  const fetchTasks = async () => {
    try {
      loading.value = true
      error.value = ''
      const token = localStorage.getItem('token')
      
      if (!token) {
        console.error('No token found')
        router.push('/login')
        return
      }

      // 检查 token 格式
      if (!token.match(/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/)) {
        console.error('Token 格式不正确，重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
        return
      }

      // 确保 token 格式正确
      const authToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      console.log('发送请求，使用 token:', authToken.substring(0, 20) + '...')

      const response = await axios.get('http://8.148.68.206:5000/api/tasks', {
        headers: {
          'Authorization': authToken
        }
      })
      tasks.value = response.data.tasks
    } catch (err: any) {
      console.error('获取任务列表错误:', err.response?.data || err.message)
      
      if (err.response?.status === 401 || err.response?.status === 422) {
        console.error('Token 无效或过期:', err.response?.data)
        // 在清除 token 之前先记录它，以便调试
        const invalidToken = localStorage.getItem('token')
        console.error('被清除的无效 token:', invalidToken)
        
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      }
      
      error.value = err.response?.data?.message || '获取任务列表失败'
    } finally {
      loading.value = false
    }
  }
  
  onMounted(fetchTasks)
  
  const totalPages = computed(() => Math.ceil(tasks.value.length / pageSize.value))
  
  const displayedTasks = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return tasks.value.slice(start, end)
  })
  
  const handleCreateTask = async (taskName: string) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/login')
        return
      }

      // 确保 token 格式正确
      const authToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      
      const response = await axios.post('http://8.148.68.206:5000/api/tasks', {
        name: taskName
      }, {
        headers: {
          'Authorization': authToken
        }
      })
      
      tasks.value.unshift(response.data.task)
      showCreateDialog.value = false
    } catch (err: any) {
      console.error('创建任务失败:', err)
      if (err.response?.status === 401 || err.response?.status === 422) {
        console.error('Token 无效或过期:', err.response?.data)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      }
    }
  }
  
  const navigateToTask = (taskId: number) => {
    router.push(`/task/${taskId}`)
  }
  </script>
  
  <style scoped>
  .task-list {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 24px;
  }
  
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }
  
  .task-header h2 {
    font-size: 24px;
    color: #2b3674;
    margin: 0;
  }
  
  .btn-add {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #4318FF;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
    
    &:hover {
      background: #3311cc;
    }
  }
  
  .loading, .error {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #707eae;
  }
  
  .error {
    color: #ff3b3b;
  }
  
  .task-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
    margin-bottom: 24px;
    flex: 1;
  }
  
  .task-card-wrapper {
    transition: transform 0.2s;
  }
  
  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  
  .page-btn {
    border: 1px solid #e0e5f2;
    background: white;
    border-radius: 8px;
    padding: 8px;
    cursor: pointer;
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  .page-numbers {
    display: flex;
    gap: 8px;
  }
  
  .page-number {
    width: 32px;
    height: 32px;
    border: 1px solid #e0e5f2;
    background: white;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    
    &.active {
      background: #4318FF;
      color: white;
      border-color: #4318FF;
    }
  }
  
  .page-size {
    margin-left: 16px;
    padding: 6px;
    border: 1px solid #e0e5f2;
    border-radius: 8px;
    outline: none;
  }
  </style> 