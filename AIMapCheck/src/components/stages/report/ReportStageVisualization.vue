<template>
  <div class="report-visualization">
    <!-- Loading and Error States -->
    <div v-if="loading" class="loading state-container">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span>正在加载报告信息...</span>
    </div>
    <div v-else-if="error" class="error state-container">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>

    <!-- Tabs for Reports -->
    <el-tabs v-else-if="pdfReportUrl || mdContent" v-model="activeTab" class="report-tabs">
      <el-tab-pane label="PDF 报告 (标注版)" name="pdf" v-if="pdfReportUrl">
        <div class="pdf-viewer">
          <iframe :src="pdfReportUrl" frameborder="0"></iframe>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Markdown 报告 (详细)" name="md" v-if="mdContent">
         <div class="markdown-viewer" v-html="renderedMdContent"></div>
      </el-tab-pane>
       <el-tab-pane label="无可用报告" name="none" v-if="!pdfReportUrl && mdContent === null">
         <div class="no-report state-container">
             <el-icon><Document /></el-icon>
             <p>未找到可预览的报告文件。</p>
         </div>
       </el-tab-pane>
    </el-tabs>

    <!-- Fallback if no reports and not loading/error -->
     <div v-else class="no-report state-container">
       <el-icon><Document /></el-icon>
       <p>暂无报告信息，请先生成报告。</p>
     </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { ElTabs, ElTabPane, ElIcon } from 'element-plus';
import { Document, Loading, WarningFilled } from '@element-plus/icons-vue';
// Import marked library for Markdown rendering
// 注意：你需要确保项目中安装了 marked (npm install marked @types/marked)
// 如果是在一个不能直接修改依赖的环境，这里的 import 会失败。
// 替代方案是使用 <script src="..."> 在 index.html 中引入 marked。
import { marked } from 'marked'; 
// 注意：在生产环境中，为了安全，强烈建议使用 DOMPurify 清理 marked 输出的 HTML
// import DOMPurify from 'dompurify'; 

interface StageData {
    status: string;
    progress?: number;
}
interface ReportData {
    pdf_report_url?: string;
    md_report_url?: string;
    md_content?: string; // API可以直接返回内容
}

const route = useRoute();
const taskId = parseInt(route.params.id as string);

const loading = ref(false);
const error = ref<string | null>(null);
const pdfReportUrl = ref<string | null>(null);
const mdReportUrl = ref<string | null>(null); // Store URL even if content is fetched
const mdContent = ref<string | null>(null); // Store fetched/provided Markdown content
const activeTab = ref('pdf'); // Default tab

// --- Fetch Task Stage Data ---
const stageData = ref<StageData | null>(null);
const getStageData = async () => {
  try {
      const response = await axios.get<{ stage: StageData }>(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/5`); // Assuming stage 5 is report
      stageData.value = response.data.stage;
      return response.data.stage;
  } catch (err) {
       console.error("获取阶段数据失败:", err);
       // Handle error appropriately, maybe set an error state
       return null;
  }
};

// --- Fetch Report URLs/Content ---
const fetchReportStatus = async () => {
  if (!taskId) return;
  
  try {
    loading.value = true;
    error.value = null;
    pdfReportUrl.value = null;
    mdReportUrl.value = null;
    mdContent.value = null; // Reset content

    const response = await axios.get<ReportData>(
      `http://8.148.68.206:5000/api/tasks/${taskId}/report`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );

    const data = response.data;

    // Set PDF URL
    if (data.pdf_report_url) {
      pdfReportUrl.value = `http://8.148.68.206:5000${data.pdf_report_url}`;
    }

    // Handle Markdown
    mdReportUrl.value = `http://8.148.68.206:5000${data.md_report_url}`

    if (data.md_content) {
        // If API provides content directly
        mdContent.value = data.md_content;
    } else if (mdReportUrl.value) {
        // If API provides URL, fetch the content
        await fetchMarkdownContent(mdReportUrl.value);
    }
    
    // Set default active tab
    if (pdfReportUrl.value) {
      activeTab.value = 'pdf';
    } else if (mdContent.value !== null) {
      activeTab.value = 'md';
    } else {
      activeTab.value = 'none'; // Or handle this case differently
    }
    
  } catch (err: any) {
    console.error('获取报告状态失败:', err);
    error.value = '获取报告状态失败: ' + (err.response?.data?.message || err.message);
    // Ensure state reflects failure
    pdfReportUrl.value = null;
    mdReportUrl.value = null;
    mdContent.value = null;
  } finally {
    loading.value = false;
  }
};

// --- Fetch Markdown Content from URL ---
const fetchMarkdownContent = async (url: string) => {
    try {
        const response = await axios.get<string>(url, { 
            // Might not need auth if served as static file, adjust if needed
            // headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } 
            responseType: 'text' // Ensure we get plain text
        });
        mdContent.value = response.data;
    } catch (err: any) {
         console.error(`获取 Markdown 内容失败 (${url}):`, err);
         // Optionally set a specific error or leave mdContent as null
         error.value = `无法加载 Markdown 报告内容: ${err.message}`; 
         mdContent.value = null; // Ensure it's null on fetch failure
    }
};

// --- Render Markdown ---
const renderedMdContent = computed(() => {
  if (mdContent.value) {
    // IMPORTANT: Sanitize this output in production using DOMPurify or similar!
    // return DOMPurify.sanitize(marked(mdContent.value)); 
    try {
      return marked(mdContent.value); 
    } catch (e) {
       console.error("Markdown 解析错误:", e);
       return "<p>Markdown 内容解析出错。</p>";
    }
  }
  return ''; // Return empty string if no content
});


// --- Lifecycle and Exposure ---
onMounted(async () => {
  const currentStageData = await getStageData();
  // Fetch reports immediately if stage is already completed
  if (currentStageData?.status === 'completed') { 
    await fetchReportStatus(); 
  } 
  // Otherwise, rely on the parent component (TaskMonitor) 
  // calling the exposed fetchReportStatus when the stage completes.
});

defineExpose({
  fetchReportStatus // Expose method for parent component to trigger refresh
});

</script>

<style scoped>
.report-visualization {
  height: 100%;
  padding: 12px;
  display: flex;
  flex-direction: column;
}

.state-container { /* Common style for loading, error, no-report */
  flex-grow: 1; /* Take remaining space */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  color: #a3aed0;
  text-align: center;
}

.state-container .el-icon {
  font-size: 48px;
}

.loading .el-icon.is-loading { /* Specific loading style */
  animation: rotate 1.8s linear infinite;
}

.error { /* Specific error style */
  color: #f1416c;
}
.error .el-icon { /* Match icon color to text */
   color: #f1416c;
}

.report-tabs {
  flex-grow: 1; /* Allow tabs to fill height */
  display: flex;
  flex-direction: column;
}

/* Make tab content fill remaining space */
:deep(.el-tabs__content) {
  flex-grow: 1;
  height: 0; /* Important for flex-grow in column layout */
}
:deep(.el-tab-pane) {
  height: 100%;
  display: flex; /* Ensure content within pane can flex */
  flex-direction: column;
}

.pdf-viewer {
  flex: 1; /* Take available space within tab */
  min-height: 0;
  /* background: white; */
  /* border-radius: 8px; */
  /* box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08); */
  overflow: hidden;
  border: 1px solid #e0e5f2; /* Add subtle border */
}

.pdf-viewer iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.markdown-viewer {
  flex: 1; /* Take available space within tab */
  overflow-y: auto; /* Allow scrolling for long markdown */
  padding: 20px;
  background-color: #ffffff;
  border: 1px solid #e0e5f2;
  border-radius: 4px;
  line-height: 1.7;
  font-size: 14px;
  color: #333;
}

/* Add some basic styling for rendered Markdown */
.markdown-viewer :deep(h1),
.markdown-viewer :deep(h2),
.markdown-viewer :deep(h3),
.markdown-viewer :deep(h4) {
  color: #2b3674;
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}
.markdown-viewer :deep(h1) { font-size: 1.8em; }
.markdown-viewer :deep(h2) { font-size: 1.5em; }
.markdown-viewer :deep(h3) { font-size: 1.3em; }
.markdown-viewer :deep(h4) { font-size: 1.1em; border-bottom: none;}

.markdown-viewer :deep(p) {
  margin-bottom: 1em;
}

.markdown-viewer :deep(ul),
.markdown-viewer :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1em;
}

.markdown-viewer :deep(li) {
  margin-bottom: 0.4em;
}

.markdown-viewer :deep(code) {
  background-color: #f4f7fe;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.markdown-viewer :deep(pre) {
  background-color: #f4f7fe;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
}
.markdown-viewer :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-viewer :deep(blockquote) {
  border-left: 4px solid #dce1ef;
  padding-left: 1em;
  margin-left: 0;
  color: #707eae;
}

.markdown-viewer :deep(table) {
  border-collapse: collapse;
  margin-bottom: 1em;
  width: auto; /* Or 100% if needed */
}
.markdown-viewer :deep(th),
.markdown-viewer :deep(td) {
  border: 1px solid #dce1ef;
  padding: 0.5em 0.8em;
}
.markdown-viewer :deep(th) {
  background-color: #f8f9fc;
  font-weight: 600;
}
.markdown-viewer :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}


@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>