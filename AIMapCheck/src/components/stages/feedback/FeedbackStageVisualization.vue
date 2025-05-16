<template>
  <div class="feedback-visualization">
    <el-card class="box-card instructions-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>如何提供有效反馈</span>
          <el-icon><QuestionFilled /></el-icon>
        </div>
      </template>
      <p>为了帮助我们改进平台和模型，请在右侧面板提供具体、清晰的反馈：</p>
      <ul>
        <li>
          <strong>选择准确的类别：</strong> 这有助于我们将问题分配给合适的团队。
        </li>
        <li>
          <strong>详细描述问题：</strong>
          <ul>
             <li>如果是【分析结果错误(错检)】或【分析结果错误(漏检)】，请尽可能描述错误的位置、涉及的规则类型（如"道路悬挂"、"建筑压盖"等）、以及您认为正确的结果。如果可能，请在"相关信息"中提供审查报告中的错误ID。</li>
             <li>如果是【规则库问题】，请指明是通用规则还是您的个人规则，并说明具体问题或改进建议。</li>
             <li>如果是【模型性能】，请描述在哪些场景下性能不佳（如速度慢、特定地物识别差等）。</li>
          </ul>
        </li>
         <li>
           <strong>提供相关信息：</strong> 任何有助于复现或理解问题的补充信息（错误ID、截图描述等）都非常有价值。
         </li>
        <li>
          <strong>提出具体建议：</strong> 如果您有关于如何改进的建议，请在"改进建议"中说明。
        </li>
      </ul>
      <p>
          如果您对本次审查结果没有疑问或建议，可以直接点击右侧面板底部的"无反馈，标记完成"按钮。
      </p>
    </el-card>

     <!-- Section to display submitted feedback (Requires Backend Endpoint) -->
     <el-card class="box-card submitted-feedback-card" shadow="never" v-if="!isLoadingFeedback && submittedFeedbacks.length > 0">
         <template #header>
            <div class="card-header">
              <span>已提交的反馈记录</span>
              <el-icon><ChatLineSquare /></el-icon>
            </div>
         </template>
         <div v-for="(fb, index) in submittedFeedbacks" :key="fb.id || index" class="feedback-item">
             <p><strong>类别:</strong> {{ getCategoryText(fb.category) }}</p>
             <p v-if="fb.related_info"><strong>相关信息:</strong> {{ fb.related_info }}</p>
             <p><strong>描述:</strong> {{ fb.description }}</p>
             <p v-if="fb.suggestion"><strong>建议:</strong> {{ fb.suggestion }}</p>
             <div v-if="fb.image_url" class="feedback-image-container">
                 <el-image
                    style="max-height: 100%; height: auto; max-width: 200px; border-radius: 4px; cursor: pointer;"
                    :src="`${API_BASE_URL}${fb.image_url}`"
                    fit="contain"
                    hide-on-click-modal
                    preview-teleported
                    alt="反馈截图"
                 />
             </div>
             <!-- <p class="feedback-time"><i>提交于: {{ formatDateTime(fb.created_at) }}</i></p> -->
         </div>
     </el-card>
     <el-empty v-else-if="!isLoadingFeedback && submittedFeedbacks.length === 0" description="暂无已提交的反馈记录"></el-empty>
     <div v-if="isLoadingFeedback" style="text-align: center; padding: 30px; color: #909399;">正在加载反馈记录...</div> 

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElCard, ElIcon, ElEmpty } from 'element-plus';
import { QuestionFilled, ChatLineSquare } from '@element-plus/icons-vue';
import axios from 'axios';
import { useRoute } from 'vue-router';

interface SubmittedFeedback {
    id: number;
    category: string;
    related_info?: string;
    description: string;
    suggestion?: string;
    image_url?: string;
    created_at: string; // Assuming backend returns ISO string
}
const route = useRoute();
const taskId = computed(() => parseInt(route.params.id as string));
const API_BASE_URL = 'http://8.148.68.206:5000'; // Use your actual base URL

const submittedFeedbacks = ref<SubmittedFeedback[]>([]);
const isLoadingFeedback = ref(false);

// Map category keys to display text
const categoryTextMap: Record<string, string> = {
    'analysis_error_false_positive': '分析结果错误 (错检)',
    'analysis_error_missed': '分析结果错误 (漏检)',
    'rule_library_issue': '规则库问题/建议',
    'model_performance': '模型性能问题',
    'ui_ux_issue': 'UI/UX 问题',
    'other': '其他建议'
};
const getCategoryText = (categoryKey: string): string => {
    return categoryTextMap[categoryKey] || categoryKey;
};

// Format date/time string
const formatDateTime = (isoString: string): string => {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleString();
    } catch (e) {
        return isoString; // Return original if parsing fails
    }
};

// Fetch submitted feedback (Requires Backend Endpoint)
const fetchSubmittedFeedback = async () => {
    if (!taskId.value) return;
    isLoadingFeedback.value = true;
    try {
        // TODO: Create this endpoint GET '/api/tasks/:taskId/feedback' in backend
        const response = await axios.get<SubmittedFeedback[]>(`${API_BASE_URL}/api/tasks/${taskId.value}/feedback`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        submittedFeedbacks.value = response.data || [];
    } catch (error: any) {
        console.error("获取已提交反馈失败:", error);
        // Don't show error message to user, just show empty state
        submittedFeedbacks.value = [];
    } finally {
        isLoadingFeedback.value = false;
    }
};

onMounted(() => {
    fetchSubmittedFeedback();
});

</script>

<style scoped>
.feedback-visualization {
  padding: 20px;
  background-color: #f9faff; /* Light background for the visualization area */
  display: flex;
  flex-direction: column;
  gap: 20px;

}

.box-card {
  border: 1px solid #e0e5f2;
  border-radius: 8px;
}

:deep(.el-card__header) {
  background-color: #fcfdff;
  border-bottom: 1px solid #e0e5f2;
  padding: 12px 20px; /* Adjust padding */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #2b3674;
  font-weight: 600;
  font-size: 16px;
}
.card-header .el-icon {
    font-size: 18px;
    color: #707eae;
}

.instructions-card p {
    margin: 0 0 12px;
    color: #555e85;
    line-height: 1.7;
    font-size: 14px;
}
.instructions-card p:last-of-type {
    margin-bottom: 0;
}

.instructions-card ul {
    margin: 12px 0 12px 20px;
    padding: 0;
    list-style-type: disc;
    color: #555e85;
    font-size: 14px;
    line-height: 1.7;
}

.instructions-card ul li {
    margin-bottom: 10px;
}
.instructions-card ul li ul {
    list-style-type: circle;
    margin-top: 6px;
    margin-left: 15px;
}
.instructions-card ul li ul li {
    margin-bottom: 4px;
}


.submitted-feedback-card .feedback-item {
    padding: 15px 0;
    border-bottom: 1px dashed #e0e5f2;
}
.submitted-feedback-card .feedback-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
.submitted-feedback-card .feedback-item p {
    margin: 0 0 8px;
    color: #555e85;
    font-size: 14px;
    line-height: 1.6;
    word-wrap: break-word; /* Allow long words to wrap */
}
.submitted-feedback-card .feedback-item p strong {
    color: #2b3674;
    margin-right: 5px;
}
.submitted-feedback-card .feedback-item .feedback-time {
    font-size: 12px;
    color: #a3aed0;
    margin-top: 5px;
    margin-bottom: 0;
}
.el-empty {
    padding: 40px 0; /* Adjust padding for empty state */
}

</style>