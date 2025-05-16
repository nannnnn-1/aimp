<template>
  <div class="stage-detail">
    <div class="panel-overlay" @click="$emit('close')"></div>
    <div class="panel-content">
      <div class="panel-header">
        <h3>问题反馈</h3>
        <button class="close-btn" @click="$emit('close')">
          <el-icon><Close /></el-icon>
        </button>
      </div>

      <div class="panel-body">
        <div class="status-section">
          <div class="status-badge" :class="stageData?.status">
            {{ getStatusText(stageData?.status || '') }}
          </div>
          <div v-if="stageData?.progress !== undefined && stageData?.status !== 'completed'" class="progress-bar">
            <div class="progress-fill" :style="{ width: `${stageData.progress}%` }"></div>
            <span class="progress-text">{{ stageData.progress }}%</span>
          </div>
        </div>

        <div class="description-section">
          <p>在此阶段，您可以针对本次地图审查的结果或流程提交反馈。请选择反馈类别并详细描述您的问题或建议。</p>
          <p>如果您对审查结果满意，可以直接标记此阶段为完成。</p>
        </div>

        <!-- Structured Feedback Form -->
        <el-form
          ref="feedbackFormRef"
          :model="feedbackData"
          :rules="feedbackRules"
          label-position="top"
          class="feedback-form"
          v-if="!isCompleted"
        >
          <el-form-item label="反馈类别" prop="category">
            <el-select v-model="feedbackData.category" placeholder="请选择反馈类别" style="width: 100%;">
              <el-option label="分析结果错误 (错检)" value="analysis_error_false_positive"></el-option>
              <el-option label="分析结果错误 (漏检)" value="analysis_error_missed"></el-option>
              <el-option label="规则库问题/建议" value="rule_library_issue"></el-option>
              <el-option label="模型性能问题" value="model_performance"></el-option>
              <el-option label="UI/UX 问题" value="ui_ux_issue"></el-option>
              <el-option label="其他建议" value="other"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="相关信息 (可选)" prop="related_info">
            <el-input
              v-model="feedbackData.related_info"
              placeholder="如涉及具体错误，请提供错误ID、位置等文字描述"
              clearable
            />
            <div class="input-tip">文字描述相关信息。下方可上传截图（可选）。</div>
          </el-form-item>

          <el-form-item label="相关截图 (可选)">
            <el-upload
              action="#"
              list-type="picture-card"
              :limit="1"
              :auto-upload="false"
              :on-change="handleFeedbackImageChange"
              :on-remove="handleFeedbackImageRemove"
              v-model:file-list="feedbackImageList"
              accept="image/*"
            >
              <el-icon><Plus /></el-icon>
              <template #tip>
                <div class="el-upload__tip">
                  上传截图有助于说明问题 (仅限1张图片)
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="详细描述" prop="description">
            <el-input
              v-model="feedbackData.description"
              type="textarea"
              :rows="5"
              placeholder="请详细描述您遇到的问题或您的建议..."
              required
            />
          </el-form-item>

          <el-form-item label="改进建议 (可选)" prop="suggestion">
            <el-input
              v-model="feedbackData.suggestion"
              type="textarea"
              :rows="3"
              placeholder="您希望我们如何改进？"
            />
          </el-form-item>

          <el-form-item class="form-actions">
             <el-button
              type="primary"
              :loading="isSubmittingFeedback"
              @click="submitFeedbackForm"
            >
              提交反馈
            </el-button>
          </el-form-item>
        </el-form>

        <div v-else class="completion-message">
           <el-icon><CircleCheckFilled /></el-icon>
           <span>此阶段已完成。</span>
        </div>


        <div class="actions">
           <el-button
            :loading="isCompletingStage"
            :disabled="isSubmittingFeedback || isCompleted"
            @click="completeStageDirectly"
          >
             {{ isCompleted ? '阶段已完成' : '无反馈，标记完成' }}
          </el-button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElIcon, ElUpload } from 'element-plus';
import { Close, CircleCheckFilled, Plus } from '@element-plus/icons-vue';
import axios from 'axios';
import { useRoute } from 'vue-router';
import type { FormInstance, FormRules, UploadProps, UploadUserFile, UploadFile } from 'element-plus';

interface StageData {
    status: string;
    progress?: number;
}

interface FeedbackData {
    category: string;
    related_info: string;
    description: string;
    suggestion: string;
}

const API_BASE_URL = 'http://8.148.68.206:5000';

const route = useRoute();
const taskId = computed(() => parseInt(route.params.id as string));
const stageData = ref<StageData | null>(null);
const feedbackFormRef = ref<FormInstance>();
const isSubmittingFeedback = ref(false);
const isCompletingStage = ref(false);

const feedbackData = reactive<FeedbackData>({
    category: '',
    related_info: '',
    description: '',
    suggestion: '',
});

const feedbackImageList = ref<UploadUserFile[]>([]);
const feedbackImageRaw = ref<File | null>(null);

const feedbackRules = reactive<FormRules<FeedbackData>>({
    category: [{ required: true, message: '请选择反馈类别', trigger: 'change' }],
    description: [{ required: true, message: '请填写详细描述', trigger: 'blur' }],
});

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'stage_updated'): void;
  (e: 'feedback_submitted'): void; // NEW: Event specifically after feedback is POSTed
  (e: 'feedback_completed'): void;
}>();

const statusMap: Record<string, string> = {
  'pending': '待处理',
  'in_progress': '处理中',
  'completed': '已完成',
  'error': '错误'
};

const getStatusText = (status: string) => statusMap[status] || status;

const isCompleted = computed(() => stageData.value?.status === 'completed');

const getStageData = async () => {
  if (!taskId.value) return;
  try {
    const response = await axios.get(`${API_BASE_URL}/api/tasks/${taskId.value}/stage/6`);
    stageData.value = response.data.stage;
  } catch (error) {
     console.error("获取反馈阶段状态失败:", error);
     ElMessage.error("获取阶段状态失败");
     stageData.value = { status: 'error' };
  }
};

onMounted(getStageData);

// --- Image Upload Handlers (REVISED) ---
const handleFeedbackImageChange: UploadProps['onChange'] = (uploadFile: UploadFile, uploadFiles: UploadUserFile[]) => {
  // 1. Update the display list (keep only the last one)
  feedbackImageList.value = uploadFiles.length > 0 ? [uploadFiles[uploadFiles.length - 1]] : [];

  // 2. Get the raw file from the *last* file in the list maintained by el-upload
  if (feedbackImageList.value.length > 0 && feedbackImageList.value[0].raw) {
      feedbackImageRaw.value = feedbackImageList.value[0].raw;
      console.log('Image selected/updated:', feedbackImageRaw.value?.name); // Log name here
  } else {
      // If the list is empty or the last file has no raw property, clear the raw ref
      feedbackImageRaw.value = null;
      console.log('Image selection cleared or raw file not available.');
  }
};

const handleFeedbackImageRemove: UploadProps['onRemove'] = (uploadFile: UploadFile, uploadFiles: UploadUserFile[]) => {
    feedbackImageRaw.value = null;
    feedbackImageList.value = []; // Ensure list is visually empty
    console.log('Image removed');
};

const submitFeedbackForm = async () => {
    if (!feedbackFormRef.value || !taskId.value) return;

    try {
        await feedbackFormRef.value.validate();
        isSubmittingFeedback.value = true;

        const formData = new FormData();
        formData.append('category', feedbackData.category);
        formData.append('description', feedbackData.description);
        if (feedbackData.related_info) {
            formData.append('related_info', feedbackData.related_info);
        }
        if (feedbackData.suggestion) {
            formData.append('suggestion', feedbackData.suggestion);
        }

        // if (feedbackImageRaw.value) {
        //     formData.append('feedback_image', feedbackImageRaw.value);
        // }
        console.log('Checking image file before appending (in submit):', feedbackImageRaw.value); // Keep this log
        if (feedbackImageRaw.value) {
          formData.append('feedback_image', feedbackImageRaw.value);
          console.log('Appended feedback_image to FormData');
        } else {
          console.log('No image file found in feedbackImageRaw.value to append.');
        }
        await axios.post(
            `${API_BASE_URL}/api/tasks/${taskId.value}/feedback/submit`,
            formData,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                }
            }
        );

        ElMessage.success('反馈提交成功！');
        feedbackFormRef.value.resetFields();
        feedbackImageList.value = [];
        feedbackImageRaw.value = null;
        emit('feedback_submitted')

    } catch (error: any) {
         if (error && error.fields) {
            console.log('表单验证失败:', error);
        } else {
            console.error('提交反馈失败:', error);
            ElMessage.error('提交反馈失败: ' + (error.response?.data?.message || error.message));
        }
    } finally {
        isSubmittingFeedback.value = false;
    }
};

const completeStage = async (showSuccessMsg = true) => {
    if (!taskId.value || isCompletingStage.value) return;

    isCompletingStage.value = true;
    try {
        await axios.post(
            `${API_BASE_URL}/api/tasks/${taskId.value}/feedback/complete`,
            {},
            { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }
        );

        if (showSuccessMsg) {
           ElMessage.success('反馈阶段已标记为完成！');
        }
        await getStageData();
        emit('feedback_completed');

    } catch (error: any) {
         console.error('标记完成失败:', error);
         ElMessage.error('标记完成失败: ' + (error.response?.data?.message || error.message));
    } finally {
         isCompletingStage.value = false;
    }
};

const completeStageDirectly = () => {
    completeStage();
};

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
  width: 450px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.panel-header {
  padding: 18px 24px;
  border-bottom: 1px solid #e0e5f2;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: #2b3674;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #707eae;
  cursor: pointer;
  padding: 4px;
}

.close-btn:hover {
  color: #2b3674;
}

.panel-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-badge {
  display: inline-flex;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  align-self: flex-start;
}

.status-badge.pending { background: #f4f7fe; color: #a3aed0; }
.status-badge.in_progress { background: #e9f7ff; color: #009ef7; }
.status-badge.completed { background: #e6f6f4; color: #05cd99; }
.status-badge.error { background: #fff5f8; color: #f1416c; }

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
  color: #555e85;
  line-height: 1.7;
  font-size: 14px;
  padding-bottom: 10px;
  border-bottom: 1px dashed #e0e5f2;
}

.description-section p {
  margin: 0 0 10px;
}

.description-section p:last-child {
  margin-bottom: 0;
}

.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-tip {
  font-size: 12px;
  color: #a3aed0;
  margin-top: 4px;
  line-height: 1.4;
}

.form-actions {
  margin-top: 10px;
  margin-bottom: 0;
}

.form-actions .el-form-item__content {
  justify-content: flex-start;
}

.completion-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background-color: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
  border-radius: 4px;
  font-size: 14px;
}

.completion-message .el-icon {
  font-size: 18px;
}

.actions {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #e0e5f2;
  display: flex;
  justify-content: flex-end;
}

/* Style the upload component */
:deep(.el-upload--picture-card) {
    width: 100px;
    height: 100px;
    line-height: 110px;
}
:deep(.el-upload-list--picture-card .el-upload-list__item) {
     width: 100px;
     height: 100px;
}
:deep(.el-upload-list--picture-card .el-upload-list__item-thumbnail) {
    object-fit: contain;
}
.el-upload__tip {
    line-height: 1.4;
    margin-top: 5px;
    font-size: 12px;
    color: #909399;
}
</style> 