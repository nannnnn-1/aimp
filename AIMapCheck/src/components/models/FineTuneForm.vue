<template>
  <div class="fine-tune-form-container">
    <el-alert
      title="微调说明"
      type="info"
      description="请提供模型名称、选择基础模型、上传通用样本数据 (.zip)。您还可以选择性地将部分或全部个人规则库中的规则及其样本纳入微调，以增强模型对您特定错误的识别能力。微调过程可能需要一些时间。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px;"
    />
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      label-position="right"
      @submit.prevent="submitFineTune(formRef)"
    >
      <el-form-item label="模型名称" prop="name">
        <el-input v-model="formData.name" placeholder="例如：城区道路优化模型 V1" clearable />
      </el-form-item>
      <el-form-item label="模型描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="简要描述模型的用途、训练数据特点等 (可选)"
          clearable
        />
      </el-form-item>
      <el-form-item label="选择基础模型" prop="base_model_id">
        <el-select
          v-model="formData.base_model_id"
          placeholder="请选择一个基础模型"
          style="width: 100%"
          filterable
          clearable
          :loading="isLoadingBaseModels"
        >
          <el-option
            v-for="model in baseModels"
            :key="model.id"
            :label="`${model.name} (${model.id})`"
            :value="model.id"
          >
           <span style="float: left">{{ model.name }}</span>
           <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px;">
               {{ model.id }}
           </span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="选择个人规则" prop="selected_user_rule_ids">
         <div style="display: flex; align-items: center; gap: 10px;">
            <el-button type="primary" plain :icon="EditPen" @click="openRuleSelectionDialog">
                选择要纳入微调的个人规则
            </el-button>
            <el-tag v-if="formData.selected_user_rule_ids.length > 0" type="success" size="small" effect="light">
                已选择 {{ formData.selected_user_rule_ids.length }} 条规则
            </el-tag>
             <el-tag v-else type="info" size="small" effect="light">未选择任何个人规则</el-tag>
              <el-tooltip placement="top">
                  <template #content>
                      点击按钮从您的个人规则库中<br/>
                      选择要包含在本次微调中的规则。<br/>
                      (可选，不选择则只使用上传的样本数据)
                  </template>
                  <el-icon style="cursor: help; color: #909399; margin-left: 5px;"><InfoFilled /></el-icon>
             </el-tooltip>
         </div>
      </el-form-item>

      <el-form-item label="上传样本数据" prop="sample_data_ref">
        <el-upload
          class="sample-data-uploader"
          drag
          action="http://8.148.68.206:5000/api/models/fine-tune/upload"
          :headers="uploadHeaders"
          name="sample_data"
          :before-upload="handleBeforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :on-remove="handleRemove"
          :on-exceed="handleExceed"
          :limit="1"
          :file-list="fileList"
          accept=".zip"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 .zip 文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              请上传包含样本数据的 .zip 文件 (用于优化通用规则识别)，大小不超过 100MB。
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="isSubmitting" :disabled="isSubmitDisabled">
          开始微调
        </el-button>
        <el-button @click="resetForm(formRef)">重置表单</el-button>
      </el-form-item>
    </el-form>

    <el-dialog
       v-model="ruleSelectionDialogVisible"
       title="选择要纳入微调的个人规则"
       width="65%"
       top="5vh"
       :close-on-click-modal="false"
       append-to-body
     >
       <div v-loading="isLoadingUserRules" element-loading-text="正在加载您的规则...">
           <div v-if="!isLoadingUserRules && userRules.length === 0" style="text-align: center; padding: 30px; color: #909399;">
               您尚未创建任何个人规则。
           </div>
           <div v-else-if="!isLoadingUserRules && userRules.length > 0">
               <el-alert title="提示" type="info" show-icon :closable="false" style="margin-bottom: 15px;">
                   勾选您希望用于本次模型微调的个人规则。模型将学习识别这些规则对应的错误类型。
               </el-alert>
               <el-checkbox-group v-model="tempSelectedRuleIds">
                   <el-table :data="userRules" border style="width: 100%" max-height="55vh" row-key="id">
                       <el-table-column width="55" align="center">
                           <template #default="scope">
                               <el-checkbox :label="scope.row.id" :value="scope.row.id" size="large"></el-checkbox>
                           </template>
                       </el-table-column>
                       <el-table-column prop="error_type" label="错误类型" sortable show-overflow-tooltip></el-table-column>
                       <el-table-column prop="error_category" label="错误类别" sortable show-overflow-tooltip></el-table-column>
                       <el-table-column prop="layer_name" label="所属图层" show-overflow-tooltip></el-table-column>
                       <el-table-column label="操作" width="80" align="center">
                           <template #default="scope">
                               <el-button :icon="View" size="small" circle title="查看详情"></el-button>
                           </template>
                       </el-table-column>
                   </el-table>
               </el-checkbox-group>
               <div style="margin-top: 15px; text-align: right; font-size: 14px; color: #606266;">
                   已选择: <el-tag type="success" size="small">{{ tempSelectedRuleIds.length }}</el-tag> / {{ userRules.length }} 条规则
               </div>
           </div>
       </div>

       <template #footer>
         <span class="dialog-footer">
           <el-button @click="handleRuleSelectionCancel">取 消</el-button>
           <el-button type="primary" @click="handleRuleSelectionConfirm" :disabled="isLoadingUserRules">确 定</el-button>
         </span>
       </template>
     </el-dialog>

  </div>
</template>
<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'; // Added watch
import axios from 'axios';
import {
  ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton,
  ElUpload, ElMessage, ElAlert, ElDialog, ElTable, ElTableColumn, ElCheckbox, ElCheckboxGroup, // Added Dialog, Table, Checkbox etc.
  ElIcon, ElTooltip, ElTag, // Added Tag, Tooltip
  type UploadProps, type UploadRawFile, type UploadUserFile, type FormInstance, type FormRules
} from 'element-plus';
import { UploadFilled, EditPen, View } from '@element-plus/icons-vue'; // Added EditPen, View

// Interface for user rules (adjust based on actual fields from API)
interface UserRule {
    id: number;
    error_type: string;
    error_category?: string;
    layer_name?: string;
    // Add other relevant fields for display if needed
}

interface BaseModel {
  id: string;
  name: string;
  description?: string;
}

interface FineTuneFormState {
  name: string;
  description: string;
  base_model_id: string;
  sample_data_ref: string | null;
  // Replace boolean flag with array of selected rule IDs
  selected_user_rule_ids: number[];
}

// Define emits
const emit = defineEmits(['fine-tune-submitted']);

const formRef = ref<FormInstance>();
const formData = reactive<FineTuneFormState>({
  name: '',
  description: '',
  base_model_id: '',
  sample_data_ref: null,
  selected_user_rule_ids: [], // Initialize as empty array
});
const baseModels = ref<BaseModel[]>([]);
const isLoadingBaseModels = ref(false);
const isSubmitting = ref(false);
const fileList = ref<UploadUserFile[]>([]);

// --- State for Rule Selection Dialog ---
const userRules = ref<UserRule[]>([]);
const isLoadingUserRules = ref(false);
const ruleSelectionDialogVisible = ref(false);
const tempSelectedRuleIds = ref<number[]>([]); // Store selections within the dialog temporarily

const rules = reactive<FormRules<FineTuneFormState>>({
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  base_model_id: [{ required: true, message: '请选择基础模型', trigger: 'change' }],
  sample_data_ref: [{ required: true, message: '请上传样本数据文件 (.zip)', trigger: 'change' }], // Validate the ref presence
  // No validation needed for selected_user_rule_ids unless you want to enforce selection sometimes
});

// Computed property to disable submit button (remains the same)
const isSubmitDisabled = computed(() => {
  return !formData.name || !formData.base_model_id || !formData.sample_data_ref || isSubmitting.value;
});

// Fetch base models (remains the same)
const fetchBaseModels = async () => {
  isLoadingBaseModels.value = true;
  try {
    const response = await axios.get<BaseModel[]>('http://8.148.68.206:5000/api/base-models');
    baseModels.value = response.data;
     // Set default base model if available and none is selected
     if (baseModels.value.length > 0 && !formData.base_model_id) {
         // formData.base_model_id = baseModels.value[0].id; // Optionally select first model
     }
  } catch (error) {
    console.error('获取基础模型失败:', error);
    ElMessage.error('获取基础模型列表失败');
  } finally {
    isLoadingBaseModels.value = false;
  }
};
fetchBaseModels();


// --- Functions for Rule Selection Dialog ---
const fetchUserRules = async () => {
    // Don't refetch if dialog is already open and rules are loaded
    if (isLoadingUserRules.value || (userRules.value.length > 0 && ruleSelectionDialogVisible.value)) return;
    isLoadingUserRules.value = true;
    userRules.value = []; // Clear previous results before fetching
    try {
        const token = localStorage.getItem('token');
        const response = await axios.get<UserRule[]>(`http://8.148.68.206:5000/api/rules?scope=user`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (Array.isArray(response.data)) {
            userRules.value = response.data;
        } else {
             userRules.value = [];
             console.warn("User rules API did not return an array:", response.data);
             ElMessage.warning('获取用户规则列表格式错误');
        }
    } catch (err: any) {
        console.error("获取用户规则失败:", err);
        ElMessage.error(err.response?.data?.message || '无法加载您的规则数据');
        userRules.value = [];
    } finally {
        isLoadingUserRules.value = false;
    }
};

const openRuleSelectionDialog = async () => {
    await fetchUserRules(); // Ensure rules are loaded/refreshed
    if (userRules.value.length === 0 && !isLoadingUserRules.value) {
        ElMessage.info('您还没有创建任何个人规则。');
        return;
    }
    // Initialize temporary selection with current form selection
    tempSelectedRuleIds.value = [...formData.selected_user_rule_ids];
    ruleSelectionDialogVisible.value = true;
};

const handleRuleSelectionConfirm = () => {
    formData.selected_user_rule_ids = [...tempSelectedRuleIds.value];
    ruleSelectionDialogVisible.value = false;
};

const handleRuleSelectionCancel = () => {
    ruleSelectionDialogVisible.value = false;
    // tempSelectedRuleIds is reset when dialog opens next time
};

// --- Upload Handlers (remain the same) ---
const handleBeforeUpload: UploadProps['beforeUpload'] = (rawFile: UploadRawFile) => {
  if (!rawFile.name.toLowerCase().endsWith('.zip')) {
    ElMessage.error('只能上传 .zip 格式的样本文件！');
    return false;
  }
  if (rawFile.size / 1024 / 1024 > 100) { // Limit size (e.g., 100MB)
    ElMessage.error('文件大小不能超过 100MB！');
    return false;
  }
  formData.sample_data_ref = null; // Reset ref before new upload attempt
  return true;
};
const handleUploadSuccess: UploadProps['onSuccess'] = (response, uploadFile) => {
  console.log("Upload successful:", response);
  if (response && response.success && response.file_ref) {
    formData.sample_data_ref = response.file_ref;
    ElMessage.success('样本数据上传成功！');
    // Ensure fileList reflects the single uploaded file
    fileList.value = [uploadFile].filter(f => f.status === 'success'); // Keep only the successful one
    formRef.value?.validateField('sample_data_ref'); // Trigger validation update
  } else {
    ElMessage.error(response?.message || '文件上传成功，但无法获取文件引用');
    fileList.value = fileList.value.filter(f => f.uid !== uploadFile.uid); // Remove failed upload from list
    formData.sample_data_ref = null;
  }
};
const handleUploadError: UploadProps['onError'] = (error, uploadFile) => {
    console.error("Upload error:", error);
    let message = '文件上传失败';
    try {
        // Attempt to parse error message from backend response if available
        const responseData = JSON.parse(error.message || '{}');
        message = responseData.message || message;
    } catch (e) { /* ignore parsing errors, stick with default message */ }
    ElMessage.error(message);
    // Remove the file from the list on error
    fileList.value = fileList.value.filter(f => f.uid !== uploadFile.uid);
    formData.sample_data_ref = null;
};
const handleRemove: UploadProps['onRemove'] = (uploadFile, uploadFiles) => {
  // This handler is called *after* the file is removed from the internal list
  if (formData.sample_data_ref) {
      console.log('File removed, clearing sample_data_ref');
  }
  formData.sample_data_ref = null;
  fileList.value = []; // Ensure fileList is empty after removal
  // Manually trigger validation again if removing the file should make the form invalid
  formRef.value?.validateField('sample_data_ref');
};
const handleExceed: UploadProps['onExceed'] = (files) => {
  ElMessage.warning(`只能上传一个样本文件，请先移除当前文件再尝试上传`);
};

// --- Form Submission ---
const submitFineTune = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;

  try {
      await formEl.validate();

      isSubmitting.value = true;
      try {
        const token = localStorage.getItem('token');
        if (!token) throw new Error('用户未登录');

        // Send selected_user_rule_ids instead of include_user_rules
        const payload = {
          name: formData.name,
          description: formData.description,
          base_model_id: formData.base_model_id,
          sample_data_ref: formData.sample_data_ref,
          selected_user_rule_ids: formData.selected_user_rule_ids, // Send the array
        };

        console.log("Submitting payload:", payload); // Debugging

        const response = await axios.post('http://8.148.68.206:5000/api/models/fine-tune/start', payload, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 202 && response.data.model_id) {
           emit('fine-tune-submitted', {
               success: true,
               modelId: response.data.model_id,
               message: response.data.message || '微调任务已启动'
           });
          formEl.resetFields(); // Reset form fields
          fileList.value = []; // Clear upload list
          formData.sample_data_ref = null; // Explicitly clear ref
          formData.selected_user_rule_ids = []; // Reset selected rules array
        } else {
           emit('fine-tune-submitted', {
                success: false,
                message: response.data.message || '启动微调任务失败'
            });
          ElMessage.error(response.data.message || '启动微调任务失败');
        }
      } catch (err: any) {
        console.error('提交微调任务失败:', err);
        const message = err.response?.data?.message || err.message || '提交失败，请检查网络或联系管理员';
        emit('fine-tune-submitted', { success: false, message: message });
        ElMessage.error(message);
      } finally {
        isSubmitting.value = false;
      }
  } catch (validationErrors) {
       console.log('表单验证失败:', validationErrors);
       // ElMessage is automatically shown by el-form validation, no need for extra message here
       // ElMessage.warning('请检查表单填写是否完整');
  }
};


const resetForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  formEl.resetFields();
  fileList.value = []; // Clear upload list on reset
  formData.sample_data_ref = null; // Explicitly clear ref
  formData.selected_user_rule_ids = []; // Reset selected rules array
};

const uploadHeaders = computed(() => {
    const token = localStorage.getItem('token');
    // Return null or empty object if no token, axios might handle it better
    if (!token) return {};
    return {
        'Authorization': `Bearer ${token}`
    };
});
</script>



<style scoped>
.fine-tune-form-container {
  padding: 20px;
  max-width: 800px;
  margin: 20px auto; /* Add some top/bottom margin */
  background-color: #fff; /* Add background for clarity if needed */
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); /* Optional shadow */
}

.sample-data-uploader {
    width: 100%;
}
:deep(.el-upload-dragger) {
    width: 100%;
    padding: 40px 20px; /* Adjust padding */
    background-color: #fafafa; /* Lighter background */
    border: 1px dashed #dcdfe6;
    transition: border-color 0.3s;
}
:deep(.el-upload-dragger:hover) {
    border-color: var(--el-color-primary);
}

.el-upload__tip {
    line-height: 1.4;
    margin-top: 5px;
    font-size: 12px;
    color: #909399;
}

:deep(.el-dialog__body) {
    padding-top: 10px;
    padding-bottom: 20px;
}

/* Style for the checkbox column header if needed */
:deep(.el-table__header-wrapper th .el-checkbox) {
    display: none; /* Hide header checkbox if row selection is sufficient */
}

/* Ensure table cells don't wrap excessively */
:deep(.el-table .cell) {
    white-space: nowrap;
}
</style>