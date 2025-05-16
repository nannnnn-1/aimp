<template>
    <div v-if="model" class="model-details-display">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="名称">{{ model.name }}</el-descriptions-item>
        <el-descriptions-item label="ID">
          {{ model.id }}
          <el-tag size="small" :type="isBaseModel ? 'info' : 'success'" effect="light" style="margin-left: 8px;">
            {{ isBaseModel ? '基础' : '微调' }}
          </el-tag>
        </el-descriptions-item>
  
        <el-descriptions-item label="描述" :span="2">{{ model.description || '暂无描述' }}</el-descriptions-item>
  
        <!-- Fields specific to Fine-tuned Models -->
        <template v-if="!isBaseModel && 'base_model_id' in model">
          <el-descriptions-item label="基础模型">{{ model.base_model_id }}</el-descriptions-item>
          <el-descriptions-item label="最终状态">
              <el-tag :type="getStatusTagType(model.status)" size="small">
                   {{ formatStatus(model.status) }}
               </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTimestamp(model.creation_timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatTimestamp(model.completion_timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="样本数据引用" :span="2">{{ model.sample_data_ref || '-' }}</el-descriptions-item>
          <el-descriptions-item label="模型文件路径" :span="2">{{ model.model_path || '-' }}</el-descriptions-item>
        </template>
         <template v-else>
           <el-descriptions-item label="类型" :span="2">平台基础模型</el-descriptions-item>
         </template>
  
        <!-- Metrics (Common to both, if base models have them) -->
        <el-descriptions-item label="评估指标" :span="2">
            <pre v-if="model.metrics && Object.keys(model.metrics).length > 0">{{ formatMetricsForDisplay(model.metrics) }}</pre>
            <span v-else>暂无指标数据</span>
        </el-descriptions-item>
  
      </el-descriptions>
    </div>
    <div v-else class="loading-placeholder">
        加载模型信息中...
    </div>
  </template>
  
  <script setup lang="ts">
  import { computed, PropType } from 'vue';
  import { ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus';
  // Define types locally or import if path is correct
  interface BaseModel {
    id: string;
    name: string;
    description?: string;
    metrics?: Record<string, any>;
  }
  interface Model {
    id: number;
    user_id: number;
    name: string;
    description?: string;
    base_model_id: string;
    status: 'creating' | 'fine-tuning' | 'ready' | 'failed';
    model_path?: string;
    sample_data_ref?: string;
    creation_timestamp: string;
    completion_timestamp?: string;
    metrics?: Record<string, any>;
  }
  
  // --- Props ---
  const props = defineProps({
    model: {
      // Use a more generic type to accept both, or a union type
      type: Object as PropType<Partial<Model> & Partial<BaseModel> | null>,
      required: true,
    }
  });
  
  // --- Computed ---
  const isBaseModel = computed(() => {
      // Determine if it's a base model based on the ID type or presence of specific fields
      return typeof props.model?.id === 'string';
  });
  
  // --- Helpers ---
  const formatTimestamp = (timestamp: string | undefined | null): string => {
    if (!timestamp) return 'N/A';
    try { const date = new Date(timestamp); return isNaN(date.getTime()) ? '无效日期' : date.toLocaleString(); }
    catch (e) { return '日期格式错误'; }
  };
  
  const formatStatus = (status: Model['status'] | undefined): string => {
      if (!status) return '未知';
      const map: Record<Model['status'], string> = { 'creating': '创建中', 'fine-tuning': '处理中', 'ready': '准备就绪', 'failed': '失败' };
      return map[status] || status;
  };
  
  const getStatusTagType = (status: Model['status'] | undefined): 'primary' | 'warning' | 'success' | 'danger' | 'info' => {
       if (!status) return 'info';
       const map: Record<Model['status'], 'primary' | 'warning' | 'success' | 'danger' | 'info'> = { 'creating': 'primary', 'fine-tuning': 'warning', 'ready': 'success', 'failed': 'danger' };
       return map[status] || 'info';
  };
  
  const formatMetricsForDisplay = (metrics: Record<string, any> | undefined | null): string => {
      if (!metrics || Object.keys(metrics).length === 0) return '-';
      try { return JSON.stringify(metrics, null, 2); }
      catch { return '无法解析指标'; }
  };
  
  </script>
  
  <style scoped>
  .model-details-display {
      /* Add any specific styling for this component container if needed */
      padding: 5px; /* Add slight padding */
  }
  .el-descriptions {
      margin-top: 0; /* Remove default top margin if added by parent */
  }
  pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      background-color: #f8f9fa;
      padding: 10px 15px;
      border-radius: 4px;
      border: 1px solid #dee2e6;
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.85em;
      line-height: 1.6;
      max-height: 200px;
      overflow-y: auto;
      margin: 0; /* Reset margin */
  }
  .loading-placeholder{
      text-align: center;
      color: #909399;
      padding: 20px;
  }
  </style>