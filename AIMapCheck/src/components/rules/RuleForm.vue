<!-- src/components/rules/RuleForm.vue -->
<template>
    <el-form ref="ruleFormRef" :model="formData" :rules="formRules" label-position="top">
      <el-row :gutter="20">
         <el-col :span="12">
            <el-form-item label="错误类型" prop="error_type">
               <el-input v-model="formData.error_type" placeholder="请输入错误类型：" :disabled="isEditing"></el-input>
            </el-form-item>
         </el-col>
         <el-col :span="12">
            <el-form-item label="错误类别" prop="error_category">
               <el-input v-model="formData.error_category" placeholder="例如: 拓扑关系"></el-input>
            </el-form-item>
          </el-col>
      </el-row>
       <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="所属图层" prop="layer_name">
               <el-input v-model="formData.layer_name" placeholder="例如: roads_layer"></el-input>
             </el-form-item>
           </el-col>
           <el-col :span="12">
              <el-form-item label="严重级别" prop="severity">
                <el-select v-model="formData.severity" placeholder="请选择严重级别" style="width: 100%;">
                  <el-option label="高" value="高"></el-option>
                  <el-option label="中" value="中"></el-option>
                  <el-option label="低" value="低"></el-option>
                </el-select>
              </el-form-item>
           </el-col>
       </el-row>
  
      <el-form-item label="错误描述" prop="description">
        <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="详细描述该错误类型的特征"></el-input>
      </el-form-item>
  
      <el-form-item label="解决方法" prop="solution">
        <el-input v-model="formData.solution" type="textarea" :rows="3" placeholder="描述如何修正此类错误"></el-input>
      </el-form-item>
  
      <el-row :gutter="20">
         <el-col :span="12">
             <el-form-item label="错误样本 (可选)">
                 <el-upload
                   action="#"
                   list-type="picture-card"
                   :limit="1"
                   :auto-upload="false"
                   :on-change="(file, list) => handleFileChange(file, list, 'before')"
                   :on-remove="(file, list) => handleFileRemove('before')"
                   v-model:file-list="fileLists.before"
                 >
                   <el-icon><Plus /></el-icon>
                 </el-upload>
             </el-form-item>
         </el-col>
         <el-col :span="12">
             <el-form-item label="正确样本 (可选)">
                 <el-upload
                   action="#"
                   list-type="picture-card"
                   :limit="1"
                   :auto-upload="false"
                   :on-change="(file, list) => handleFileChange(file, list, 'after')"
                   :on-remove="(file, list) => handleFileRemove('after')"
                   v-model:file-list="fileLists.after"
                  >
                   <el-icon><Plus /></el-icon>
                 </el-upload>
             </el-form-item>
         </el-col>
    </el-row>
  
  
      <el-form-item style="margin-top: 20px;">
        <el-button @click="$emit('cancel')">取 消</el-button>
        <el-button type="primary" @click="submitForm" :loading="isSubmitting">
          {{ isEditing ? '更新规则' : '创建规则' }}
        </el-button>
      </el-form-item>
    </el-form>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, watch, onMounted } from 'vue';
  import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElUpload, ElIcon, ElMessage, ElRow, ElCol } from 'element-plus';
  import type { FormInstance, FormRules, UploadProps, UploadUserFile, UploadFile, UploadRawFile } from 'element-plus';
  import { Plus } from '@element-plus/icons-vue';
  import axios from 'axios';
  
  const props = defineProps<{
    ruleData?: any | null; // Pass existing rule data for editing
  }>();
  
  const emit = defineEmits(['cancel', 'success']);
  
  const ruleFormRef = ref<FormInstance>();
  const isSubmitting = ref(false);
  const isEditing = ref(false);
  
  const formData = reactive({
      id: null, // For editing
      error_type: '',
      error_category: '',
      layer_name: '',
      severity: '',
      description: '',
      solution: '',
  });
  
// Use 'before' and 'after' keys
const fileLists = reactive<{ before: UploadUserFile[], after: UploadUserFile[] }>({
    before: [],
    after: []
});
// Store the actual File objects selected by the user
const filesToUpload = reactive<{ before?: File, after?: File }>({}); // Use 'before' and 'after'
  
  
  const formRules = reactive<FormRules>({
      error_type: [{ required: true, message: '请输入错误类型', trigger: 'blur' }],
      error_category: [{ required: true, message: '请输入错误类别', trigger: 'blur' }],
      layer_name: [{ required: true, message: '请输入所属图层', trigger: 'blur' }],
      severity: [{ required: true, message: '请选择严重级别', trigger: 'change' }],
      description: [{ required: true, message: '请输入错误描述', trigger: 'blur' }],
      solution: [{ required: true, message: '请输入解决方法', trigger: 'blur' }],
  });
  
  // --- File Handling ---
  const handleFileChange = (uploadFile: UploadFile, uploadFiles: UploadUserFile[], type: 'before' | 'after') => {
       // Keep only the last selected file for single upload limit
       fileLists[type] = uploadFiles.slice(-1);
       // Store the raw file for later upload
       if (uploadFile.raw) {
          filesToUpload[type] = uploadFile.raw;
       } else {
           delete filesToUpload[type]; // Remove if file is removed or invalid
       }
       console.log(`File changed for ${type}:`, filesToUpload);
  };
  
  const handleFileRemove = (type: 'before' | 'after') => {
      delete filesToUpload[type];
       console.log(`File removed for ${type}:`, filesToUpload);
       // Also potentially clear existing image URL if editing? Needs more logic
  };
  
  // --- Form Submission ---
  const submitForm = async () => {
    if (!ruleFormRef.value) return;
    try {
      await ruleFormRef.value.validate();
      isSubmitting.value = true;
  
      const fd = new FormData();
      // Append text data
      Object.entries(formData).forEach(([key, value]) => {
          // Don't send ID for creation, maybe not needed for update if in URL
          if (key !== 'id' && value !== null && value !== undefined) {
               fd.append(key, String(value));
          }
      });
  
      // Append files
      Object.entries(filesToUpload).forEach(([key, file]) => {
           if(file) {
               // Use key names expected by backend (e.g., image_standard)
               const backendKey = `image_${key}`;
               fd.append(backendKey, file);
           }
      });
      console.log(formData)
      const API_BASE_URL = 'http://8.148.68.206:5000';
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'multipart/form-data' };
  
      let response;
      if (isEditing.value && formData.id) {
        // Update existing rule (PUT or PATCH)
         console.log('Updating rule with ID:', formData.id);
         response = await axios.put(`${API_BASE_URL}/api/rules/${formData.id}`, fd, { headers });
      } else {
        // Create new rule
         console.log('Creating new rule');
         response = await axios.post(`${API_BASE_URL}/api/user-rules`, fd, { headers });
      }
  
      console.log('API Response:', response.data);
      emit('success'); // Notify parent component
  
    } catch (error: any) {
       if (error && Array.isArray(error)) {
            console.log('Form validation failed (RuleForm)');
            ElMessage.error('请检查表单输入项');
       } else {
            console.error('Rule form submission error:', error);
            ElMessage.error(error.response?.data?.message || error.message || '操作失败');
       }
    } finally {
      isSubmitting.value = false;
    }
  };
  
  // --- Populate form if editing ---
  const populateForm = (data: any) => {
       formData.id = data.id;
       formData.error_type = data.error_type || '';
       formData.error_category = data.error_category || '';
       formData.layer_name = data.layer_name || '';
       formData.severity = data.severity || '';
       formData.description = data.description || '';
       formData.solution = data.solution || '';
       
       // TODO: Populate fileLists with existing image URLs for preview
       // This requires knowing the full URL and creating UploadUserFile objects
       // Example (needs adjustment based on how URLs are stored/served):
       const getFullUrl = (relPath: string) => relPath ? `http://8.148.68.206:5000${relPath.startsWith('/') ? '' : '/'}${relPath}` : ''; // Adjust base URL/path logic
       
       const existingFiles: { [key: string]: UploadUserFile[] } = { before: [], after: []};
       if (data.image_before_url) existingFiles.before.push({ name: 'before.png', url: getFullUrl(data.image_before_url), status: 'success', uid: Date.now()+1 });
       if (data.image_after_url) existingFiles.error.push({ name: 'after.png', url: getFullUrl(data.image_after_url), status: 'success', uid: Date.now()+2 });
      
       
       fileLists.before = existingFiles.before;
       fileLists.after = existingFiles.after;
       
       // Clear filesToUpload when populating for edit, user must re-select to change
       Object.keys(filesToUpload).forEach(key => delete filesToUpload[key as keyof typeof filesToUpload]);
  };
  
  watch(() => props.ruleData, (newData) => {
      if (newData) {
          isEditing.value = true;
          populateForm(newData);
      } else {
          isEditing.value = false;
          // Reset form fields if needed when switching from edit to add
          ruleFormRef.value?.resetFields(); // Reset validation and model
           Object.assign(formData, { id: null, error_type: '', error_category: '', layer_name: '', severity: '', description: '', solution: ''}); // Manual reset
           fileLists.before = []; fileLists.after = [] // Clear file lists
           Object.keys(filesToUpload).forEach(key => delete filesToUpload[key as keyof typeof filesToUpload]); // Clear files to upload
      }
  }, { immediate: true }); // Run immediately on component mount
  
  onMounted(() => {
      // Initial population if ruleData is provided on mount
      if(props.ruleData) {
          isEditing.value = true;
          populateForm(props.ruleData);
      } else {
          isEditing.value = false;
      }
  })
  
  </script>
  
  <style scoped>
  /* Add minimal styles or rely on parent dialog */
  .el-form-item {
      margin-bottom: 18px; /* Adjust spacing */
  }
  .el-upload--picture-card { /* Adjust upload button size if needed */
      width: 100px;
      height: 100px;
      line-height: 110px;
  }
  :deep(.el-upload-list--picture-card .el-upload-list__item) { /* Adjust uploaded image size */
       width: 100px;
       height: 100px;
  }
  </style>