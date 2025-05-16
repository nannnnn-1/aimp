<template>
  <div class="sample-library-page">
    <!-- <div class="page-header">
      <h2>错误检测样例库</h2>
      <p>这里展示了平台提供的通用错误样例以及您自定义的规则。</p>
    </div> -->

    <div class="page-content">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="rule-tabs">
          <el-tab-pane label="通用规则库" name="public"></el-tab-pane>
          <el-tab-pane label="我的规则库" name="user"></el-tab-pane>
      </el-tabs>

      <div class="controls-bar">
        <div class="filters">
           <el-select
              :model-value="selectedCategory"
              @update:modelValue="selectedCategory = $event === null ? '' : $event"
              placeholder="按错误类别筛选"
              clearable
              size="default"
              style="width: 200px;"
           >
              <el-option v-for="cat in uniqueCategories" :key="cat" :label="cat" :value="cat"></el-option>
          </el-select>
          <el-input
              v-model="searchText"
              placeholder="搜索描述或类型"
              clearable
              size="default"
              style="width: 250px;"
              :prefix-icon="Search"
          />
        </div>
         <el-button
            v-if="activeTab === 'user'"
            type="primary"
            :icon="Plus"
            @click="openAddRuleDialog"
            size="default"
          >
            新增规则
          </el-button>
      </div>

      <div v-if="isLoading" class="loading-state state-container">
          <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          <span>加载 {{ activeTab === 'user' ? '我的规则' : '通用规则' }} 中...</span>
      </div>
      <div v-else-if="currentError" class="error-state state-container">
          <el-icon><WarningFilled /></el-icon>
          <span>{{ currentError }}</span>
      </div>
      <div v-else-if="filteredExamples.length === 0" class="empty-state state-container">
          <el-icon><FolderOpened /></el-icon>
          <span>
              {{ activeTab === 'user' ? '您还没有创建任何规则。' : '没有找到匹配的通用规则。' }}
          </span>
      </div>

      <el-row v-else :gutter="20" class="example-grid">
        <el-col v-for="example in filteredExamples" :key="example.id" :xs="24" :sm="12" :md="12" :lg="8" :xl="6">
          <el-card class="example-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="error-type-title">{{ example.error_type }}</span>
                 <div>
                    <el-tag size="small" type="info" effect="plain" v-if="example.error_category" style="margin-right: 8px;color:#0f0f0f">{{ example.error_category }}</el-tag>
                    <template v-if="activeTab === 'user'">
                         <el-tooltip content="编辑规则" placement="top">
                            <el-button :icon="Edit" circle size="small" @click="openEditRuleDialog(example)"></el-button>
                         </el-tooltip>
                          <el-tooltip content="删除规则" placement="top">
                            <el-button type="danger" :icon="Delete" circle size="small" @click="confirmDeleteRule(example)"></el-button>
                          </el-tooltip>
                    </template>
                </div>
              </div>
            </template>
            <!-- src/views/SampleLibrary.vue - Template section -->
            <div class="card-body">
               <div class="info-item" v-if="example.layer_name"><span class="info-label">图层:</span> <span class="info-value">{{ example.layer_name }}</span></div>
               <div class="info-item"><span class="info-label">描述:</span> <span class="info-value">{{ example.description || '-' }}</span></div>
               <div class="image-comparison">
                 <div class="image-container">
                   <p class="image-label">错误示例:</p>
                   <el-image :src="getImageUrl(example.image_before_url, activeTab === 'user')" fit="contain" lazy preview-teleported hide-on-click-modal :preview-src-list="getPreviewList(example, 'before')"><template #error><div class="image-slot"><el-icon><Picture /></el-icon>无图</div></template><template #placeholder><div class="image-slot load-anim">加载中</div></template></el-image>
                 </div>
                 <div class="image-container">
                   <p class="image-label">正确示例:</p>
                   <el-image :src="getImageUrl(example.image_after_url, activeTab === 'user')" fit="contain" lazy preview-teleported hide-on-click-modal :preview-src-list="getPreviewList(example, 'after')"><template #error><div class="image-slot"><el-icon><Picture /></el-icon>无图</div></template><template #placeholder><div class="image-slot load-anim">加载中</div></template></el-image>
                 </div>
               </div>
               <div class="info-item solution-item"><span class="info-label">解决方法:</span> <span class="info-value">{{ example.solution || '-' }}</span></div>
               <div class="info-item severity-item"><span class="info-label">严重级别:</span> <el-tag :type="getSeverityTagType(example.severity)" size="small">{{ example.severity || '未知' }}</el-tag></div>
               <div v-if="example.tags" class="tags-section"><el-tag v-for="tag in example.tags.split(',')" :key="tag" size="small" type="success" effect="plain" style="margin-right: 5px; margin-bottom: 5px;">{{ tag.trim() }}</el-tag></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

     <el-dialog
       v-model="ruleDialogVisible"
       :title="isEditing ? '编辑规则' : '新增规则'"
       width="60%"
       :close-on-click-modal="false"
       @closed="resetForm"
      >
        <RuleForm
           v-if="ruleDialogVisible"
           :rule-data="editingRule"
           @cancel="ruleDialogVisible = false"
           @success="handleRuleFormSuccess"
          />
     </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import axios from 'axios';
import { ElCard, ElRow, ElCol, ElTag, ElImage, ElSelect, ElOption, ElInput, ElIcon, ElTabs, ElTabPane, ElButton, ElDialog, ElMessage, ElMessageBox, ElTooltip } from 'element-plus';
import { Search, Loading, WarningFilled, FolderOpened, Picture, Plus, Edit, Delete } from '@element-plus/icons-vue';
import RuleForm from '@/components/rules/RuleForm.vue'; // Adjust path as needed

const API_BASE_URL = 'http://8.148.68.206:5000'; // Use a constant

interface ErrorExample {
  id: number;
  layer_name?: string;
  error_category?: string;
  error_type: string;
  description?: string;
  solution?: string;
  // Corrected Image URL fields
  image_before_url?: string; // Was image_error_url
  image_after_url?: string;  // Was image_correct_url
  // Removed: image_standard_url?
  tags?: string;
  severity?: string;
  owner_user_id?: number;
}

const activeTab = ref('public'); // 'public' or 'user'
const publicExamples = ref<ErrorExample[]>([]);
const userExamples = ref<ErrorExample[]>([]);
const isLoadingPublic = ref(false);
const isLoadingUser = ref(false);
const errorPublic = ref<string | null>(null);
const errorUser = ref<string | null>(null);
const dataLoaded = ref({ public: false, user: false }); // Track loaded state

const selectedCategory = ref(''); // Use empty string for cleared state
const searchText = ref('');

// --- Dialog State ---
const ruleDialogVisible = ref(false);
const isEditing = ref(false);
const editingRule = ref<ErrorExample | null>(null);

// --- Computed Properties ---
const isLoading = computed(() => activeTab.value === 'public' ? isLoadingPublic.value : isLoadingUser.value);
const currentError = computed(() => activeTab.value === 'public' ? errorPublic.value : errorUser.value);
const displayedExamples = computed(() => activeTab.value === 'public' ? publicExamples.value : userExamples.value);

const uniqueCategories = computed(() => {
  const cats = new Set<string>();
  displayedExamples.value.forEach(ex => {
      if (ex.error_category) cats.add(ex.error_category);
  });
  return Array.from(cats).sort();
});

const filteredExamples = computed(() => {
  // Ensure displayedExamples.value is always an array
  if (!Array.isArray(displayedExamples.value)) {
     console.warn("displayedExamples is not an array:", displayedExamples.value);
     return [];
  }
  return displayedExamples.value.filter(ex => {
      const categoryMatch = !selectedCategory.value || ex.error_category === selectedCategory.value;
      const textMatch = !searchText.value ||
                        ex.error_type.toLowerCase().includes(searchText.value.toLowerCase()) ||
                        (ex.description && ex.description.toLowerCase().includes(searchText.value.toLowerCase())) ||
                        (ex.solution && ex.solution.toLowerCase().includes(searchText.value.toLowerCase())) ||
                        (ex.layer_name && ex.layer_name.toLowerCase().includes(searchText.value.toLowerCase())) ||
                        (ex.error_category && ex.error_category.toLowerCase().includes(searchText.value.toLowerCase()));
      return categoryMatch && textMatch;
  });
});

// --- Methods ---
// getImageUrl can likely be simplified as the backend now returns full URLs
const getImageUrl = (fullUrl?: string) => {
    return API_BASE_URL + fullUrl
    // return fullUrl || ''; // Just return the URL from backend or empty string
};

// Generate preview list, ensuring valid URLs
const getPreviewList = (example: ErrorExample, type: 'before' | 'after'): string[] => {
    // Backend now returns full URLs
    const urls = [
        example.image_before_url,
        example.image_after_url
    ].filter(url => !!url) as string[]; // Filter out undefined/null/empty and assert as string[]

    // Optionally reorder so the clicked image is first
    const clickedUrl = type === 'before' ? example.image_before_url : example.image_after_url;
    if (clickedUrl && urls.includes(clickedUrl)) {
        return [clickedUrl, ...urls.filter(u => u !== clickedUrl)];
    }
    return urls;
};


const fetchPublicExamples = async () => {
  if (isLoadingPublic.value) return;
  isLoadingPublic.value = true;
  errorPublic.value = null;
  try {
      // Assuming API endpoint is /api/rules?scope=public
      const response = await axios.get<ErrorExample[]>(`${API_BASE_URL}/api/rules?scope=public`);
      if (Array.isArray(response.data)) {
          publicExamples.value = response.data;
          dataLoaded.value.public = true;
      } else {
          console.warn("Public rules API did not return an array:", response.data);
          publicExamples.value = [];
          errorPublic.value = '获取通用规则数据格式错误';
      }
  } catch (err: any) {
      console.error("获取通用规则失败:", err);
      errorPublic.value = err.response?.data?.message || err.message || '无法加载通用规则数据';
      publicExamples.value = [];
  } finally {
      isLoadingPublic.value = false;
  }
};

const fetchUserExamples = async () => {
  if (isLoadingUser.value) return;
  isLoadingUser.value = true;
  errorUser.value = null;
  try {
      // Assuming API endpoint is /api/rules?scope=user (requires auth)
      const response = await axios.get<ErrorExample[]>(`${API_BASE_URL}/api/rules?scope=user`, {
           headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
       if (Array.isArray(response.data)) {
          userExamples.value = response.data;
          dataLoaded.value.user = true;
      } else {
          console.warn("User rules API did not return an array:", response.data);
          userExamples.value = [];
          errorUser.value = '获取用户规则数据格式错误';
      }
  } catch (err: any) {
      console.error("获取用户规则失败:", err);
      errorUser.value = err.response?.data?.message || err.message || '无法加载您的规则数据';
       if (err.response?.status === 401) { // Handle unauthorized specifically
           errorUser.value = '请先登录以查看您的规则。';
       }
      userExamples.value = [];
  } finally {
      isLoadingUser.value = false;
  }
};

const handleTabChange = (tabName: string | number) => {
  // Fetch data only if it hasn't been loaded yet
  if (tabName === 'public' && !dataLoaded.value.public) {
      fetchPublicExamples();
  } else if (tabName === 'user' && !dataLoaded.value.user) {
      fetchUserExamples();
  }
};

const openAddRuleDialog = () => {
  isEditing.value = false;
  editingRule.value = null;
  ruleDialogVisible.value = true;
};

const openEditRuleDialog = (rule: ErrorExample) => {
  isEditing.value = true;
  editingRule.value = { ...rule }; // Clone rule data for editing
  ruleDialogVisible.value = true;
};

const resetForm = () => {
  editingRule.value = null; // Clear editing state when dialog closes
};

const handleRuleFormSuccess = () => {
  ruleDialogVisible.value = false;
  ElMessage.success(isEditing.value ? '规则更新成功！' : '规则创建成功！');
  // Refresh user rules list
  fetchUserExamples();
};

const confirmDeleteRule = (rule: ErrorExample) => {
   ElMessageBox.confirm(
      `确定要删除规则 "${rule.error_type}" 吗？此操作无法撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    .then(async () => {
        await deleteRule(rule.id);
    })
    .catch(() => {
        // User cancelled
        ElMessage.info('删除操作已取消');
    });
};

const deleteRule = async (ruleId: number) => {
  try {
      // Assuming DELETE /api/rules/:id (requires auth)
      await axios.delete(`${API_BASE_URL}/api/rules/${ruleId}`, {
           headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      ElMessage.success('规则删除成功！');
      // Refresh user rules list
      fetchUserExamples();
  } catch (err: any) {
       console.error("删除规则失败:", err);
       ElMessage.error(err.response?.data?.message || err.message || '删除规则失败');
  }
};

const getSeverityTagType = (severity?: string): 'danger' | 'warning' | 'info' | 'success' | '' => {
  switch (severity?.toLowerCase()) {
      case '高': return 'danger';
      case '中': return 'warning';
      case '低': return 'success'; // Using success for low severity visually
      case '提示': return 'info';
      default: return ''; // Element Plus default
  }
};


// --- Lifecycle ---
onMounted(() => {
// Fetch initial tab data
fetchPublicExamples();
});

</script>

<style scoped>
.sample-library-page { padding: 25px 30px; background-color: #f4f7fe; min-height: calc(100vh - 50px); }
.page-header { margin-bottom: 10px; padding-bottom: 15px; border-bottom: 1px solid #e0e5f2;}
.page-header h2 { margin-top: 0; margin-bottom: 5px; color: #2b3674; }
.page-header p { margin-top: 0; font-size: 0.95em; color: #707eae; }

.rule-tabs {
  margin-bottom: 5px; /* Reduce space below tabs */
}
:deep(.el-tabs__header) {
 margin-bottom: 10px; /* Space below tab headers */
}
:deep(.el-tabs__nav-wrap::after) {
  background-color: transparent; /* Hide default bottom border */
}
:deep(.el-tabs__active-bar) {
 height: 3px; /* Thicker active bar */
}

.controls-bar {
  background-color: #ffffff; padding: 15px 20px; border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); margin-bottom: 25px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;
}
.filters {
 display: flex; gap: 15px; align-items: center; flex-wrap: wrap;
}

.example-grid { /* Grid itself needs minimal styling */ }
.example-card { margin-bottom: 20px; height: 100%; border: 1px solid #e0e5f2; border-radius: 8px; transition: box-shadow 0.3s ease; display: flex; flex-direction: column; }
.example-card:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
.example-card :deep(.el-card__header) { background-color: #f8f9fc; padding: 10px 18px; border-bottom: 1px solid #e0e5f2; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.error-type-title { font-weight: 600; color: #cb2a2a; font-size: 1.05em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-header > div { display: flex; align-items: center; gap: 5px; flex-shrink: 0;} /* Ensure buttons/tags don't shrink excessively */

.card-body { padding: 15px 18px; font-size: 14px; color: #606266; flex-grow: 1; display: flex; flex-direction: column;}
.info-item { margin-bottom: 10px; line-height: 1.6; }
.info-label { font-weight: 600; color: #303133; margin-right: 6px; }
.info-value { color: #555; word-break: break-all; } /* Allow long values to wrap */
.solution-item { margin-top: 10px; padding-top: 8px; border-top: 1px dashed #eee; }
.severity-item { margin-top: 8px; }

.image-comparison { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 12px 0; }
.image-container { text-align: center; background-color: #fdfdfe; padding: 8px; border: 1px solid #f0f2f5; border-radius: 4px; }
.image-label { font-size: 0.75em; color: #a0a5b1; margin-bottom: 5px; font-weight: 500; }
.image-container .el-image { width: 100%; height: 120px; /* Adjusted height */ border-radius: 3px; background-color: #f5f7fa; display: flex; align-items: center; justify-content: center; }
.image-slot { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; width: 100%; color: #c0c4cc; font-size: 12px; gap: 4px; }
.image-slot .el-icon { font-size: 20px; }
.load-anim { animation: pulse 1.5s infinite ease-in-out; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }


.tags-section { margin-top: auto; padding-top: 8px; border-top: 1px dashed #eee; }

.state-container { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #909399; padding: 60px 20px; min-height: 300px; gap: 15px; }
.state-container .el-icon { font-size: 32px; color: #c8cdd4; }
.error-state { color: #f56c6c; } .error-state .el-icon { color: #f56c6c; }
.loading-state .el-icon.is-loading { animation: rotating 1.8s linear infinite; }
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Dialog styling */
:deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 20px;
}
</style>
