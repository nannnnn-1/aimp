<template>
  <div class="task-report-page">
    <div class="report-header">
      <h2>任务报告查看</h2>
      <!-- Optional: Add Task ID or other info here -->
    </div>

    <div class="report-view-container">
      <!-- Left Column: PDF -->
      <div class="report-column pdf-column">
        <div class="column-header">标注版 PDF 报告</div>
        <div class="column-content">
          <div v-if="loading" class="state-indicator">
            <el-icon class="is-loading"><Loading /></el-icon><span>加载中...</span>
          </div>
          <div v-else-if="error && !annotatedPdfUrl" class="state-indicator error">
             <el-icon><WarningFilled /></el-icon><span>无法加载 PDF 报告</span>
          </div>
           <div v-else-if="!annotatedPdfUrl" class="state-indicator">
             <el-icon><Document /></el-icon><span>无标注版 PDF 报告</span>
           </div>
          <iframe v-else :src="annotatedPdfUrl" frameborder="0"></iframe>
        </div>
      </div>

      <!-- Right Column: Markdown -->
      <div class="report-column markdown-column">
         <div class="column-header">详细分析报告 (Markdown)</div>
         <div class="column-content">
            <div v-if="loading" class="state-indicator">
              <el-icon class="is-loading"><Loading /></el-icon><span>加载中...</span>
            </div>
            <div v-else-if="error && !mdContent" class="state-indicator error">
               <el-icon><WarningFilled /></el-icon><span>无法加载 Markdown 报告</span>
            </div>
             <div v-else-if="!mdContent" class="state-indicator">
               <el-icon><Document /></el-icon><span>无详细分析报告</span>
             </div>
           <div v-else class="markdown-viewer" v-html="renderedMdContent"></div>
         </div>
      </div>
    </div>

    <!-- Floating Notes Widget -->
    <FloatingNotes v-if="taskId" :task-id="taskId" />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { ElIcon } from 'element-plus';
import { Document, Loading, WarningFilled } from '@element-plus/icons-vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify'; // Import DOMPurify
import FloatingNotes from '@/components/misc/FloatingNotes.vue'; // Adjust path if needed

interface ReportData {
    pdf_report_url?: string;
    md_report_url?: string;
    md_content?: string; // API might return content directly
}

const route = useRoute();
const taskId = route.params.id as string; // Assuming ID is always string initially

const loading = ref(true); // Start in loading state
const error = ref<string | null>(null);
const annotatedPdfUrl = ref<string | null>(null);
const mdReportUrl = ref<string | null>(null); // URL from API
const mdContent = ref<string | null>(null);   // Fetched/provided content

const API_BASE_URL = 'http://8.148.68.206:5000'; // Define base URL

// --- Fetch Markdown Content ---
const fetchMarkdownContent = async (url: string): Promise<string | null> => {
    try {
        const response = await axios.get<string>(url, { responseType: 'text' });
        return response.data;
    } catch (err: any) {
         console.error(`获取 Markdown 内容失败 (${url}):`, err);
         // Set specific error for the MD part if desired
         error.value = error.value ? `${error.value}\n无法加载 Markdown 内容.` : `无法加载 Markdown 内容: ${err.message}`;
         return null;
    }
};

// --- Fetch Report Data ---
const getReportData = async () => {
  if (!taskId) {
    error.value = "无效的任务 ID";
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = null;
  annotatedPdfUrl.value = null;
  mdReportUrl.value = null;
  mdContent.value = null;

  try {
    const response = await axios.get<ReportData>(
      `${API_BASE_URL}/api/tasks/${taskId}/report`,
      {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      }
    );

    const data = response.data;

    // Set Annotated PDF URL
    if (data.pdf_report_url) {
      annotatedPdfUrl.value = `${API_BASE_URL}${data.pdf_report_url}`;
    }

    // Handle Markdown
    if (data.md_content) {
        mdContent.value = data.md_content;
    } else if (data.md_report_url) {
        mdReportUrl.value = `${API_BASE_URL}${data.md_report_url}`;
        const fetchedContent = await fetchMarkdownContent(mdReportUrl.value);
        if (fetchedContent) {
            mdContent.value = fetchedContent;
        }
        // If fetchMarkdownContent failed, error state is already set inside it
    }

    // Check if at least one report loaded
    if (!annotatedPdfUrl.value && !mdContent.value && !error.value) {
         error.value = "未找到任何报告文件。"; // Set specific error if API returns empty valid response
    }

  } catch (err: any) {
    console.error('获取报告数据失败:', err);
    error.value = '获取报告数据失败: ' + (err.response?.data?.message || err.message);
  } finally {
    loading.value = false;
  }
};

// --- Render Markdown ---
const renderedMdContent = computed(() => {
  if (mdContent.value) {
    try {
      // Sanitize the HTML generated by marked
      const rawHtml = marked(mdContent.value);
      return DOMPurify.sanitize(rawHtml); // Use DOMPurify
    } catch (e) {
       console.error("Markdown 解析错误:", e);
       return "<p style='color: red;'>Markdown 内容解析出错。</p>"; // Display error inline
    }
  }
  return '';
});

// --- Lifecycle ---
onMounted(() => {
  getReportData();
});

</script>

<style scoped>
.task-report-page {
  padding: 20px;
  height: calc(100vh - 60px); /* Adjust based on your layout's header height */
  display: flex;
  flex-direction: column;
  background-color: #f4f7fe; /* Light background for page */
}

.report-header {
  margin-bottom: 15px;
  flex-shrink: 0; /* Prevent header from shrinking */
}

.report-header h2 {
  font-size: 22px;
  color: #2b3674;
  margin: 0;
}

.report-view-container {
  flex-grow: 1; /* Take remaining vertical space */
  display: flex;
  gap: 15px;
  min-height: 0; /* Important for flex children with height % or flex-grow */
}

.report-column {
  flex: 1; /* Each column takes half the space */
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden; /* Prevent content overflow */
  min-width: 0; /* Important for flex items */
}

.column-header {
  padding: 10px 15px;
  font-weight: 600;
  color: #344767;
  border-bottom: 1px solid #e0e5f2;
  flex-shrink: 0; /* Prevent header shrinking */
  background-color: #f8f9fc;
}

.column-content {
  flex-grow: 1; /* Content area fills column */
  position: relative; /* For absolute positioning of state indicators if needed */
  overflow: hidden; /* For iframe/scroll */
  display: flex; /* To center state indicators */
  flex-direction: column; /* Needed for iframe height */
}

.column-content iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.markdown-viewer {
  height: 100%; /* Fill the column content area */
  overflow-y: auto; /* Allow scrolling */
  padding: 15px 20px;
  line-height: 1.7;
  font-size: 14px;
  color: #333;
}

.state-indicator {
  margin: auto; /* Center indicator vertically and horizontally */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #a3aed0;
  padding: 20px;
  text-align: center;
}

.state-indicator .el-icon {
  font-size: 36px;
}
.state-indicator.error {
  color: #f1416c;
}
.state-indicator.error .el-icon {
  color: #f1416c;
}
.state-indicator .el-icon.is-loading {
  animation: rotate 1.8s linear infinite;
}


/* Markdown specific styles (copied from previous example, adjust as needed) */
.markdown-viewer :deep(h1), .markdown-viewer :deep(h2), .markdown-viewer :deep(h3), .markdown-viewer :deep(h4) {
    color: #2b3674; margin-top: 1.5em; margin-bottom: 0.8em; border-bottom: 1px solid #eee; padding-bottom: 0.3em;
}
.markdown-viewer :deep(h1) { font-size: 1.6em; } .markdown-viewer :deep(h2) { font-size: 1.4em; }
.markdown-viewer :deep(h3) { font-size: 1.2em; } .markdown-viewer :deep(h4) { font-size: 1em; border-bottom: none; }
.markdown-viewer :deep(p) { margin-bottom: 1em; }
.markdown-viewer :deep(ul), .markdown-viewer :deep(ol) { padding-left: 2em; margin-bottom: 1em; }
.markdown-viewer :deep(li) { margin-bottom: 0.4em; }
.markdown-viewer :deep(code) { background-color: #f4f7fe; padding: 0.2em 0.4em; border-radius: 3px; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; }
.markdown-viewer :deep(pre) { background-color: #f4f7fe; padding: 1em; border-radius: 4px; overflow-x: auto; }
.markdown-viewer :deep(pre code) { background-color: transparent; padding: 0; }
.markdown-viewer :deep(blockquote) { border-left: 4px solid #dce1ef; padding-left: 1em; margin-left: 0; color: #707eae; }
.markdown-viewer :deep(table) { border-collapse: collapse; margin-bottom: 1em; width: auto; }
.markdown-viewer :deep(th), .markdown-viewer :deep(td) { border: 1px solid #dce1ef; padding: 0.5em 0.8em; }
.markdown-viewer :deep(th) { background-color: #f8f9fc; font-weight: 600; }
.markdown-viewer :deep(img) { max-width: 100%; height: auto; border-radius: 4px; margin-top: 0.5em; margin-bottom: 0.5em; background-color: #f8f9fc; border: 1px solid #eee;}


@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>