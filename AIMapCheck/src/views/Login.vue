<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <img src="../../public/images/logo2.png" alt="Logo" class="logo">
        <h1>AI地图检测系统</h1>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label>用户名</label>
          <input
            type="text"
            v-model="username"
            placeholder="请输入用户名"
            required
          >
        </div>

        <div class="form-item">
          <label>密码</label>
          <input
            type="password"
            v-model="password"
            placeholder="请输入密码"
            required
          >
        </div>

        <div class="error-message" v-if="errorMsg">{{ errorMsg }}</div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
      </form>
      <div class="footer-links">
         <span>没有账户？</span>
         <el-link type="primary" @click="goToRegister">立即注册</el-link>
         <span class="separator">|</span>
         <el-link type="default" @click="goToPortal">返回门户</el-link>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)

const handleLogin = async () => {
  try {
    isLoading.value = true
    errorMsg.value = ''
    
    console.log('开始登录请求...')
    const response = await axios.post('http://8.148.68.206:5000/api/login', {
      username: username.value,
      password: password.value
    })
    
    console.log('登录响应:', response.data)
    
    // 检查 token 格式
    if (!response.data.token || typeof response.data.token !== 'string') {
      throw new Error('服务器返回的 token 格式不正确')
    }
    
    // 检查 token 是否是有效的 JWT 格式（应该是三段由点分隔的字符串）
    if (!response.data.token.match(/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/)) {
      console.warn('Token 可能不是有效的 JWT 格式:', response.data.token)
    }
    
    // 存储token和用户信息
    // 确保 token 不包含 'Bearer ' 前缀
    const token = response.data.token.replace('Bearer ', '')
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    
    console.log('Token已保存:', token.substring(0, 20) + '...')
    
    // 登录成功后跳转到首页
    router.push('/home')
  } catch (error: any) {
    console.error('登录错误:', error)
    errorMsg.value = error.response?.data?.message || error.message || '登录失败，请重试'
  } finally {
    isLoading.value = false
  }
}
// --- Added Navigation Methods ---
const goToRegister = () => {
  router.push('/register'); // Navigate to Register page
};

const goToPortal = () => {
  router.push('/'); // Navigate to Portal page (root)
};
// --- End Added Navigation Methods ---
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  height: 64px;
  margin-bottom: 16px;
}

.login-header h1 {
  color: #2b3674;
  font-size: 24px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  color: #2b3674;
  font-size: 14px;
}

.form-item input {
  padding: 12px;
  border: 1px solid #e0e5f2;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: #4318FF;
  }
}

.error-message {
  color: #ff3b3b;
  font-size: 14px;
  text-align: center;
}

.login-btn {
  background: #4318FF;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover:not(:disabled) {
    background: #3311cc;
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
/* === Added Footer Links Style === */
.footer-links {
  margin-top: 25px; /* Add space above links */
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
/* === End Added Footer Links Style === */
</style> 