<template>
  <header class="header">
    <div class="search">
      <i class="fas fa-search"></i>
      <input type="text" placeholder="搜索...">
    </div>
    
    <div class="user-info">
      
      
      <div class="user" @click="showUserMenu = !showUserMenu">
        <img 
          :src="userAvatar" 
          :alt="userName" 
          class="avatar"
          @error="handleAvatarError"
        >
        <span class="name">{{ userName }}</span>
        <i class="fas fa-chevron-down"></i>
        
        <div class="user-menu" v-if="showUserMenu" @mouseleave="showUserMenu = false">
          <div class="menu-item">
            <i class="fas fa-user"></i>
            个人信息
          </div>
          <div class="menu-item">
            <i class="fas fa-cog"></i>
            设置
          </div>
          <div class="menu-item" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i>
            退出登录
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showUserMenu = ref(false)
const userAvatar = ref('https://api.dicebear.com/7.x/avataaars/svg?seed=default')
const userName = ref('')

const handleAvatarError = () => {
  console.error('Avatar failed to load:', userAvatar.value)
  // 加载失败时使用默认头像
  userAvatar.value = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userName.value || 'default'}`
}

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      userName.value = user.real_name || user.username
      console.log('User data:', user)
      
      if (user.avatar_url) {
        console.log('Original avatar URL:', user.avatar_url)
        if (user.avatar_url.startsWith('http')) {
          userAvatar.value = user.avatar_url
        } else {
          // 确保文件名正确
          const filename = user.avatar_url.split('\\').pop().split('/').pop()
          const avatarUrl = `http://8.148.68.206:5000/api/avatars/${filename}`
          console.log('Constructed avatar URL:', avatarUrl)
          userAvatar.value = avatarUrl
        }
      } else {
        console.log('No avatar URL, using default')
        userAvatar.value = `https://api.dicebear.com/7.x/avataaars/svg?seed=default`
      }
    } catch (error) {
      console.error('Error parsing user data:', error)
      userAvatar.value = `https://api.dicebear.com/7.x/avataaars/svg?seed=default`
    }
  }
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: 50px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #e0e5f2;
}

.search {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f4f7fe;
  padding: 8px 16px;
  border-radius: 12px;
  width: 300px;
}

.search input {
  border: none;
  background: none;
  outline: none;
  font-size: 14px;
  color: #2b3674;
  width: 100%;
  
  &::placeholder {
    color: #a3aed0;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.notifications {
  position: relative;
  cursor: pointer;
}

.badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #ff3b3b;
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
}

.user {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  position: relative;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  object-fit: cover;
}

.name {
  font-weight: 500;
}

.user-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 8px;
  min-width: 180px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  color: #2b3674;
  transition: background 0.2s;
  border-radius: 8px;
  
  &:hover {
    background: #f4f7fe;
  }
  
  i {
    color: #4318FF;
  }
}
</style> 