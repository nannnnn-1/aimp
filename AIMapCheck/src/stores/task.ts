import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface TaskItem {
  id: number
  name: string
  status: 'pending' | 'in_progress' | 'completed'
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  assignee?: string
}

interface TaskFilter {
  search: string
  status: string[]
  dateRange: [Date | null, Date | null]
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskItem[]>([
    {
      id: 1,
      name: '完成网站首页设计',
      status: 'in_progress',
      dueDate: '2024-04-10',
      priority: 'high',
      assignee: '张三'
    },
    {
      id: 2,
      name: '优化后端API性能',
      status: 'pending',
      dueDate: '2024-04-15',
      priority: 'medium',
      assignee: '李四'
    },
    {
      id: 3,
      name: '编写测试用例',
      status: 'completed',
      dueDate: '2024-04-05',
      priority: 'low',
      assignee: '王五'
    }
  ])

  const filters = ref<TaskFilter>({
    search: '',
    status: [],
    dateRange: [null, null]
  })

  const pagination = ref({
    currentPage: 1,
    pageSize: 10,
    total: 3
  })

  const filteredTasks = computed(() => {
    let result = [...tasks.value]
    
    // Apply search filter
    if (filters.value.search) {
      result = result.filter(task => 
        task.name.toLowerCase().includes(filters.value.search.toLowerCase()) ||
        task.assignee?.toLowerCase().includes(filters.value.search.toLowerCase())
      )
    }

    // Apply status filter
    if (filters.value.status.length > 0) {
      result = result.filter(task => filters.value.status.includes(task.status))
    }

    // Apply date filter
    if (filters.value.dateRange[0] && filters.value.dateRange[1]) {
      result = result.filter(task => {
        const taskDate = new Date(task.dueDate)
        return taskDate >= filters.value.dateRange[0]! && 
               taskDate <= filters.value.dateRange[1]!
      })
    }

    pagination.value.total = result.length

    // Apply pagination
    const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
    const end = start + pagination.value.pageSize

    return result.slice(start, end)
  })

  function updateFilter(newFilters: Partial<TaskFilter>) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.currentPage = 1 // Reset to first page when filters change
  }

  function updatePagination(page: number, size?: number) {
    pagination.value.currentPage = page
    if (size !== undefined) {
      pagination.value.pageSize = size
    }
  }

  return {
    tasks,
    filters,
    pagination,
    filteredTasks,
    updateFilter,
    updatePagination
  }
})
