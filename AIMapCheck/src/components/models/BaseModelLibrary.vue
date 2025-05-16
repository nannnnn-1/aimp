<template>
    <div class="base-model-library">
      <div class="toolbar">
        <el-button type="primary" @click="fetchBaseModels" :loading="isLoading" :icon="Refresh">
          刷新列表
        </el-button>
      </div>
  
      <el-table
        :data="baseModels"
        v-loading="isLoading"
        style="width: 100%"
        height="100%"
        empty-text="暂无基础模型信息"
        @row-click="handleViewDetails"
        highlight-current-row
        class="clickable-table" 
        >
        <el-table-column prop="id" label="模型 ID" width="200" sortable />
        <el-table-column prop="name" label="模型名称" width="250" sortable />
        <el-table-column prop="description" label="描述" min-width="300">
          <template #default="scope">
            {{ scope.row.description || '-' }}
          </template>
        </el-table-column>
        <!-- Add Action column for explicit details button -->
         <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
               <el-tooltip content="查看详情" placement="top">
                 <el-button
                   link
                   type="primary"
                   size="small"
                   @click.stop="handleViewDetails(scope.row)"
                 >
                   详情
                 </el-button>
               </el-tooltip>
            </template>
          </el-table-column>
      </el-table>
  
       <!-- Details Dialog for Base Models -->
        <el-dialog
          v-model="isDetailDialogVisible"
          :title="selectedBaseModel ? `基础模型详情: ${selectedBaseModel.name}` : '基础模型详情'"
          width="60%"
          top="10vh"
          append-to-body
          destroy-on-close
        >
           <!-- Use the reusable display component -->
          <ModelDetailsDisplay v-if="selectedBaseModel" :model="selectedBaseModel" />
          <div v-else>无法加载模型信息。</div> <!-- Fallback -->
  
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="isDetailDialogVisible = false">关闭</el-button>
            </span>
          </template>
        </el-dialog>
  
    </div>
  </template>
  
<script setup lang="ts">
import ModelDetailsDisplay from './ModelDetailsDisplay.vue'; // <-- Import new component
import { ref, onMounted } from 'vue';
import axios from 'axios';
// Import necessary components
import { ElTable, ElTableColumn, ElButton, ElMessage, ElDialog, ElTooltip } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
// Import the reusable details component

  
  // --- Interfaces ---
  interface BaseModel {
    id: string;
    name: string;
    description?: string;
    metrics?: Record<string, any>; // Include metrics if provided by API
  }
  
  // --- State ---
  const baseModels = ref<BaseModel[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  // State for details dialog
  const isDetailDialogVisible = ref(false);
  const selectedBaseModel = ref<BaseModel | null>(null);
  
  
  // --- API ---
  const fetchBaseModels = async () => {
    isLoading.value = true;
    error.value = null;
    try {
      // Use relative URL or env var
      const response = await axios.get<BaseModel[]>('http://8.148.68.206:5000/api/base-models');
  
      if (Array.isArray(response.data)) {
        // Fetch details (including metrics) for each base model maybe?
        // Or assume the list endpoint already provides enough info,
        // or the details component fetches additional info if needed.
        // For now, assume list endpoint gives id, name, desc. Metrics fetched on demand.
        baseModels.value = response.data;
      } else {
        console.warn('API /api/base-models did not return an array:', response.data);
        throw new Error('获取基础模型列表失败：无效的响应格式');
      }
    } catch (err: any) {
      console.error('获取基础模型列表失败:', err);
      error.value = err.message || '获取基础模型列表失败';
      ElMessage.error(error.value);
      baseModels.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  // --- Methods ---
  const handleViewDetails = async (model: BaseModel) => {
      console.log("Viewing base model details:", model);
      // Base model details might already be sufficient from the list,
      // or we might need to fetch more details (like metrics)
      // For simplicity now, assume we need to fetch full details including metrics
      isLoading.value = true; // Use main loading indicator temporarily
      try {
          // Fetch full details using the specific endpoint
           const response = await axios.get<BaseModel>(`http://8.148.68.206:5000/api/base-models/${model.id}`);
           selectedBaseModel.value = response.data; // Store the full details
           isDetailDialogVisible.value = true; // Open the dialog
      } catch (err:any) {
           console.error(`获取基础模型 ${model.id} 详情失败:`, err);
           ElMessage.error(`加载详情失败: ${err.message || '未知错误'}`);
           selectedBaseModel.value = model; // Show at least the basic info
           isDetailDialogVisible.value = true; // Still open dialog maybe? Or show error differently.
      } finally {
          isLoading.value = false;
      }
  
  
  };
  
  // --- Lifecycle ---
  onMounted(() => {
    fetchBaseModels();
  });
  </script>
  
  <style scoped>
  .base-model-library { display: flex; flex-direction: column; height: 100%; gap: 15px; }
  .toolbar { flex-shrink: 0; }
  .el-table { flex-grow: 1; }
  /* Make table rows clickable */
  .clickable-table :deep(.el-table__row) {
      cursor: pointer;
  }
  .el-table-column--operation .el-button + .el-button {
      margin-left: 8px;
  }
  </style>