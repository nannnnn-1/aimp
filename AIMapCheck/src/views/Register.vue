<template>
    <div class="register-container">
      <div class="register-box"> 
        <div class="register-header"> 
          <img src="../../public/images/logo2.png" alt="Logo" class="logo">
          <h1>创建新账户</h1>
        </div>
  
        <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            class="register-form"
            status-icon
            @submit.prevent="handleRegister"
          >
            <div class="form-item">
              <label>用户名</label>
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名 (3-15 字符)"
                required
                clearable
                :input-style="{ /* Match input styles */
                   padding: '12px',
                   border: '1px solid #e0e5f2',
                   borderRadius: '8px',
                   outline: 'none'
                }"
                 @focus="handleFocus"
                 @blur="handleBlur"
              >
              </el-input>

               <div v-if="showError && errorField === 'username'" class="validation-error">{{ errorMessage }}</div>
            </div>
  
            <div class="form-item">
               <label>密码</label>
               <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码 (至少 6 位)"
                show-password
                required
                clearable
                 :input-style="{ /* Match input styles */
                   padding: '12px',
                   border: '1px solid #e0e5f2',
                   borderRadius: '8px',
                   outline: 'none'
                }"
                 @focus="handleFocus"
                 @blur="handleBlur"
              />
            </div>
  
            <div class="form-item">
               <label>确认密码</label>
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                required
                clearable
                :input-style="{ /* Match input styles */
                   padding: '12px',
                   border: '1px solid #e0e5f2',
                   borderRadius: '8px',
                   outline: 'none'
                }"
                 @focus="handleFocus"
                 @blur="handleBlur"
              />
            </div>
  
            <div class="error-message" v-if="apiErrorMsg">{{ apiErrorMsg }}</div>
  
            <button type="submit" class="register-btn" :disabled="loading">
               {{ loading ? '注册中...' : '立即注册' }}
            </button>
          </el-form>
  
        <div class="footer-links">
          <span>已有账户？</span>

          <el-link type="primary" @click="goToLogin">立即登录</el-link>
          <span class="separator">|</span>
          <el-link type="default" @click="goToPortal">返回门户</el-link>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  // Use ElInput and ElLink for consistency, remove others if not needed by form structure
  import { ElForm, ElInput, ElButton, ElLink, ElMessage, ElIcon } from 'element-plus';
  import type { FormInstance, FormRules } from 'element-plus';
  // Removed Message icon if email is not used
  
  const router = useRouter();
  const registerFormRef = ref<FormInstance>();
  const loading = ref(false);
  const apiErrorMsg = ref(''); // For errors returned from API
  
  const registerForm = reactive({
    username: '',
    password: '',
    confirmPassword: '',
  });
  
  // --- Validation Rules ---
  const validatePassConfirm = (rule: any, value: any, callback: any) => {
    if (value === '') {
      callback(new Error('请再次输入密码'));
    } else if (value !== registerForm.password) {
      callback(new Error("两次输入的密码不一致!"));
    } else {
      callback();
    }
  };
  
  const registerRules = reactive<FormRules>({
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 15, message: '长度应在 3 到 15 个字符', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
    ],
    confirmPassword: [
      { required: true, message: '请再次输入密码', trigger: 'blur' },
      { validator: validatePassConfirm, trigger: 'blur' }
    ],
  });
  
  // --- Event Handlers ---
  const handleRegister = async () => {
    if (!registerFormRef.value) return;
    apiErrorMsg.value = ''; // Clear previous API errors
    try {
      await registerFormRef.value.validate();
      loading.value = true;
  
      const apiUrl = 'http://8.148.68.206:5000/api/register';
      const payload = {
          username: registerForm.username,
          password: registerForm.password,
      };
  
      await axios.post(apiUrl, payload);
  
      ElMessage({
        message: '注册成功！即将跳转到登录页面。',
        type: 'success',
        duration: 2000
      });
  
      setTimeout(() => { router.push('/login'); }, 2000);
  
    } catch (error: any) {
      if (error && Array.isArray(error)) {
          console.log('Form validation failed'); // Validation error from element plus handled internally now
      } else {
          // API error
          console.error('注册失败:', error);
          apiErrorMsg.value = error.response?.data?.message || error.message || '注册过程中发生错误';
      }
    } finally {
      loading.value = false;
    }
  };
  
  const goToLogin = () => { router.push('/login'); };
  const goToPortal = () => { router.push('/'); }; // Navigate to portal (root)
  
  // Add focus/blur handlers to mimic input border change
  const handleFocus = (event: FocusEvent) => {
      const inputElement = (event.target as HTMLInputElement).closest('.el-input');
      if (inputElement) {
          inputElement.classList.add('is-focused');
      }
  };
  const handleBlur = (event: FocusEvent) => {
       const inputElement = (event.target as HTMLInputElement).closest('.el-input');
      if (inputElement) {
          inputElement.classList.remove('is-focused');
      }
  };
  
  </script>
  
  <style scoped>
  .register-container { /* Changed from register-page for consistency */
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* Match Login BG */
    padding: 20px;
  }
  
  .register-box { /* Match Login Box */
    background: white;
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
  }
  
  .register-header { /* Match Login Header */
    text-align: center;
    margin-bottom: 32px;
  }
  
  .logo {
    height: 64px;
    margin-bottom: 16px;
  }
  
  .register-header h1 {
    color: #2b3674;
    font-size: 24px;
    margin: 0;
  }
  
  .register-form { /* Match Login Form */
    display: flex;
    flex-direction: column;
    gap: 20px; /* Consistent gap */
  }
  
  /* Style div wrapper like form-item */
  .form-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .form-item label {
    color: #2b3674;
    font-size: 14px;
    margin-bottom: 0; /* Let gap handle spacing */
  }
  
  /* Style el-input to look like the simple input */
  .form-item :deep(.el-input__wrapper) {
      padding: 0 !important; /* Remove el-input internal padding */
      box-shadow: none !important; /* Remove default focus shadow */
      background-color: transparent;
  }
  .form-item :deep(.el-input__inner) {
      padding: 12px !important; /* Apply padding to inner input */
      border: 1px solid #e0e5f2 !important;
      border-radius: 8px !important;
      outline: none !important;
      transition: border-color 0.2s;
      height: auto !important; /* Allow padding to dictate height */
      line-height: normal !important;
      background-color: #fff; /* Ensure background */
  }
  /* Style el-input password suffix */
  .form-item :deep(.el-input__suffix) {
      right: 12px; /* Adjust position */
  }
  /* Focus state - Apply border to the inner input */
  .form-item .el-input.is-focused :deep(.el-input__inner) {
      border-color: #4318FF !important;
  }
  /* --- End input styling --- */
  
  
  .error-message { /* Style API errors */
    color: #ff3b3b;
    font-size: 14px;
    text-align: center;
    min-height: 20px; /* Prevent layout shift */
    margin-top: -10px; /* Adjust spacing */
    margin-bottom: -5px;
  }
  
  .register-btn { /* Match Login Button */
    background: #4318FF;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
    width: 100%; /* Make button full width */
    margin-top: 15px; /* Add margin like login */
  
    &:hover:not(:disabled) {
      background: #3311cc;
    }
  
    &:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
  }
  
  .footer-links {
    margin-top: 25px; /* Adjusted margin */
    text-align: center;
    font-size: 0.9rem;
    color: #606266;
    display: flex; /* Use flex for alignment */
    justify-content: center;
    align-items: center;
    gap: 8px; /* Gap between items */
  }
  .footer-links span {
      /* margin-right: 5px; removed, use gap */
  }
  .footer-links .el-link {
      vertical-align: baseline;
  }
  .footer-links .separator { /* Style for separator */
      color: #dcdfe6;
      margin: 0 4px;
  }
  </style>