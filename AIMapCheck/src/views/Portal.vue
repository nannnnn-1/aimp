<template>
    <div class="portal-page">
        <PortalNavbar></PortalNavbar>
      <video autoplay muted loop playsinline id="bg-video">
        <source src="/videos/earth.mp4" type="video/mp4" />
        你的浏览器不支持 HTML5 视频。
      </video>
      <div class="portal-overlay"></div>
  
      <section class="hero-section">
        <div class="hero-content">
          <h1 class="main-title">AI智能审图平台</h1>
          <p class="subtitle">
            您的智能地图审查专家，提供自动化错误检测、规则管理与模型定制服务。
          </p>
        </div>
      </section>
  
      <section class="start-separator">
        <h2 class="start-text">Let's Start From Here!</h2>
        <div class="separator-line"></div>
      </section>
  
      <section class="features-section" ref="featuresSectionRef">
        <div class="timeline-container">
          <div class="guide-line-column">
            <div class="vertical-guide-line-left"></div>
          </div>
          <div class="feature-modules-column">
            <div class="feature-modules-container">
              <div
                v-for="(feature, index) in features"
                :key="feature.id"
                class="feature-module"
              >
                <div class="connector-point"></div>
                <el-card class="feature-card" shadow="always">
                   <div class="card-header-custom">
                      <div class="feature-title-bar">
                        <span class="title-decorator"></span>
                        <h3>{{ feature.title }}</h3>
                      </div>
                      <p class="feature-subtitle">{{ feature.subtitle }}</p>
                   </div>
  
                  <div class="card-content-side-by-side">
                    <div class="feature-text-content">
                      <p class="feature-description">{{ feature.description }}</p>
                      <div class="button-container">
                        <el-button type="primary" class="use-button" @click="navigateTo(feature.route)">
                          立即使用
                        </el-button>
                      </div>
                    </div>
                    <div class="feature-image-wrapper">
                       <img :src="feature.imageUrl" :alt="feature.title" loading="lazy" class="feature-image">
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </div>
        </div>
      </section>
       <footer class="portal-footer">
          <div class="footer-content">
               © {{ new Date().getFullYear() }} AI智能审图平台. All Rights Reserved.
          </div>
      </footer>
  
    </div>
  </template>
  
  <script setup lang="ts">
  import PortalNavbar from '@/components/layout/PortalNavbar.vue'; // <-- Import the navbar
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { ElButton, ElCard, ElIcon } from 'element-plus';
  // Removed unused ArrowDownBold import
  
  const router = useRouter();
  
  interface Feature {
    id: string;
    title: string;
    subtitle: string;
    description: string;
    imageUrl: string;
    route: string;
  }
  
  // TODO: Update Video Path if needed
  const videoPath = '/videos/earth.mp4';
  
  // TODO: Define your features - Ensure image paths and routes are correct
  const features = ref<Feature[]>([
  {
    id: 'task-center',
    title: '任务中心',
    subtitle: 'TASK CENTER',
    description: '创建、管理和追踪您的地图审查任务。在此上传地图数据、配置审查参数、查看任务状态并获取最终的审查报告。',
    imageUrl: '/images/portal/task-center.png', // Replace with actual image
    route: '/tasks' // Route to the main task list/management page
  },
  {
    id: 'map-review-start', // Changed ID slightly
    title: '智能审图',
    subtitle: 'INTELLIGENT REVIEW',
    description: '利用平台提供的先进AI模型对您的地图数据进行自动化错误检测。选择适用的模型、设置审查模式，快速启动审查流程。',
    imageUrl: '/images/portal/map-review.png', // Replace with actual image
    route: '/tasks' // Or a specific route to start a new task/review if available
  },
  {
    id: 'sample-library',
    title: '错误样例库',
    subtitle: 'ERROR SAMPLE LIBRARY',
    description: '浏览平台提供的通用错误检测样例，学习不同错误类型的特征和解决方法。您也可以在此创建和管理您自己的私有规则库。',
    imageUrl: '/images/portal/sample-library.png', // Replace with actual image
    route: '/sample-library' // Route to the sample library page
  },
  {
    id: 'model-hub',
    title: '模型中心',
    subtitle: 'MODEL HUB',
    description: '管理您的AI审查模型。基于平台提供的基础模型，上传您的样本数据进行微调，创建和优化针对特定审查需求的定制化模型。',
    imageUrl: '/images/portal/model-hub.png', // Replace with actual image
    route: '/models' // Route to the model management/fine-tuning page
  },
  // --- Optional Features (Uncomment and adjust if needed) ---
  // {
  //   id: 'platform-res',
  //   title: '平台资源',
  //   subtitle: 'PLATFORM RESOURCES',
  //   description: '访问平台整理的相关数据集、技术文档和其他学习资源，助力您的地图审查、模型训练与研究工作。',
  //   imageUrl: '/images/portal/platform-res.png',
  //   route: '/resources' // Ensure this route exists
  // },
  // {
  //   id: 'user-profile',
  //   title: '个人中心',
  //   subtitle: 'USER PROFILE',
  //   description: '管理您的个人信息、账户设置以及查看您的平台使用统计。',
  //   imageUrl: '/images/portal/user-center.png', // Replace with actual image
  //   route: '/profile' // Ensure this route exists
  // },
  ]);
  const featuresSectionRef = ref<HTMLElement | null>(null); // Keep ref if potentially needed
  
  const navigateTo = (routePath: string) => {
    if (routePath) {
      router.push(routePath);
    } else {
      console.warn('No route defined for this feature.');
    }
  };
  
  // scrollToFeatures might not be needed if the button is removed
  // const scrollToFeatures = () => { ... };
  
  </script>
  
  <style scoped>
  /* --- Base and Video Background --- */
  .portal-page { min-height: 100vh; background-color: #0b1120; position: relative; color: #ffffff; overflow-x: hidden;}
  #bg-video { position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; width: auto; height: auto; transform: translate(-50%, -50%); z-index: 0; object-fit: cover;}
  .portal-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(to bottom, rgba(11, 17, 32, 0.6), rgba(11, 17, 32, 0.95)); z-index: 1;}
  
  /* --- Content Sections --- */
  .hero-section, .start-separator, .features-section, .portal-footer { position: relative; z-index: 2; padding-left: 8%; padding-right: 8%; max-width: 1400px; margin-left: auto; margin-right: auto;} /* Centering content */
  
  /* 1. Hero Section */
  .hero-section { min-height: 55vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding-top: 80px; padding-bottom: 50px; }
  .hero-content { max-width: 800px; }
  .main-title { font-size: 3rem; font-weight: 700; margin-bottom: 15px; line-height: 1.3; text-shadow: 0 2px 5px rgba(0, 0, 0, 0.5); }
  .subtitle { font-size: 1.1rem; color: rgba(255, 255, 255, 0.85); margin-bottom: 0; line-height: 1.7; max-width: 600px; margin-left: auto; margin-right: auto; }
  
  /* 2. "Let's Start From Here!" Separator */
  .start-separator { text-align: center; padding: 40px 0 50px 0; display: flex; flex-direction: column; align-items: center; }
  .start-text { font-size: 1.8rem; font-weight: 600; color: #ffffff; margin-bottom: 20px; letter-spacing: 1px; }
  .separator-line { width: 80px; height: 3px; background-color: #4318FF; border-radius: 2px; }
  
  /* 3. Features Section */
  .features-section { padding-top: 10px; padding-bottom: 80px; }
  
  .timeline-container {
      display: flex;
      gap: 30px; /* Gap between line column and content column */
  }
  
  /* Left Column for the Guide Line */
  .guide-line-column {
      flex: 0 0 50px; /* Fixed width for the line area */
      position: relative; /* For positioning the line */
      /* background-color: rgba(255,0,0,0.1); */ /* Debug bg */
  }
  .vertical-guide-line-left {
      position: absolute;
      top: 10px; /* Start slightly below top */
      bottom: 10px; /* End slightly above bottom */
      left: 50%; /* Center within its column */
      transform: translateX(-50%);
      width: 2px;
      background-color: rgba(255, 255, 255, 0.15); /* Faint line color */
      z-index: 3;
  }
  
  /* Right Column for Feature Modules */
  .feature-modules-column {
      flex: 1; /* Takes remaining space */
      min-width: 0; /* Prevent flex overflow */
  }
  .feature-modules-container {
      /* Removed max-width and margin:auto */
      display: flex;
      flex-direction: column;
      gap: 30px; /* Space between cards */
  }
  
  .feature-module {
      position: relative; /* For positioning the connector point */
      padding-left: 25px; /* Space for the connector point */
      margin-bottom: 10px; /* Space below each module */
  }
  
  /* Connector point linking card to the guide line */
  .connector-point {
      position: absolute;
      left: 0; /* Align with the start of padding */
      top: 35px; /* Align vertically with card header approx */
      width: 10px;
      height: 10px;
      background-color: #4318FF; /* Accent color */
      border-radius: 50%;
      border: 2px solid rgba(255, 255, 255, 0.3); /* Optional border */
      transform: translateX(-50%); /* Center on the padding edge */
      z-index: 5; /* Above line */
  }
  
  .feature-card {
      border: none; border-radius: 16px; background-color: #ffffff;
      color: #333; overflow: hidden; position: relative;
      width: 100%; /* Card takes full width */
  }
  :deep(.el-card__body) { padding: 0 !important; }
  
  .card-header-custom { padding: 25px 30px 20px 30px; border-bottom: 1px solid #f0f2f5; }
  .feature-title-bar { display: flex; align-items: center; margin-bottom: 5px; }
  .title-decorator { width: 5px; height: 22px; background-color: #4318FF; margin-right: 12px; border-radius: 3px; }
  .card-header-custom h3 { font-size: 1.5rem; font-weight: 600; color: #2b3674; margin: 0; }
  .feature-subtitle { font-size: 0.8rem; color: #a3aed0; margin-top: 2px; margin-bottom: 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500; }
  
  .card-content-side-by-side { display: flex; align-items: stretch; gap: 30px; padding: 30px; }
  
  .feature-text-content { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: space-between; }
  .feature-description { font-size: 0.9rem; color: #555e85; line-height: 1.7; margin-bottom: 25px; }
  .button-container { margin-top: 10px; }
  .use-button { font-size: 0.9rem; }
  
  .feature-image-wrapper { flex: 0 0 48%; max-width: 48%; display: flex; align-items: center; justify-content: center; background-color: #f8f9fc; border-radius: 8px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
  .feature-image { max-width: 100%; height: auto; border-radius: 6px; object-fit: contain; }
  
  /* 4. Footer */
  .portal-footer { background-color: rgba(15, 23, 42, 0.8); color: #cbd5e1; padding: 30px 8%; text-align: center; margin-top: 40px; position: relative; z-index: 2; max-width: 1400px; margin-left: auto; margin-right: auto; } /* Centered footer */
  .footer-content { font-size: 0.9rem; color: #94a3b8; }
  
  /* --- Responsive Adjustments --- */
  @media (max-width: 992px) {
      .hero-section { min-height: auto; padding-bottom: 30px;}
      .start-separator { padding: 30px 0; }
      .timeline-container { flex-direction: column; gap: 15px; } /* Stack columns */
      .guide-line-column { display: none; } /* Hide line column */
      .feature-module { padding-left: 0; } /* Remove left padding */
      .connector-point { display: none; } /* Hide connector point */
  
      .card-content-side-by-side {
          flex-direction: column; gap: 25px; padding: 25px; align-items: center;
      }
       .feature-text-content { order: 2; width: 100%; text-align: center;}
       .feature-image-wrapper { order: 1; flex-basis: auto; max-width: 80%; margin: 0 auto; }
       .button-container { text-align: center; margin-top: 20px; }
       .feature-description { text-align: left; }
       .card-header-custom { padding: 20px 25px 15px 25px; }
       .card-header-custom h3 { font-size: 1.4rem; }
  }
  
  @media (max-width: 767px) {
    .main-title { font-size: 2rem; }
    .subtitle { font-size: 1rem; }
    .start-text { font-size: 1.5rem; }
    .feature-image-wrapper { max-width: 90%; }
    .card-header-custom h3 { font-size: 1.3rem; }
  }
  
  </style>