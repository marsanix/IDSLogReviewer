<script setup lang="ts">
import { ref } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ShieldAlert, Eye, EyeOff } from 'lucide-vue-next'
import axios from 'axios'

const emit = defineEmits(['login'])

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value.trim() || !password.value) {
    error.value = 'Please enter username and password'
    return
  }
  
  error.value = ''
  loading.value = true
  
  try {
    const res = await axios.post('/api/auth/login', {
      username: username.value.trim(),
      password: password.value
    })
    
    // Store token and emit login event
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    emit('login', res.data.user)
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background p-4">
    <Card class="w-full max-w-md">
      <CardHeader class="text-center">
        <div class="flex justify-center mb-4">
          <div class="p-3 rounded-full bg-primary/10">
            <ShieldAlert class="h-10 w-10 text-primary" />
          </div>
        </div>
        <CardTitle class="text-2xl">Si-Devi</CardTitle>
        <p class="text-sm text-muted-foreground mt-1">IDS Log Viewer</p>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="handleLogin" class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">Username</label>
            <input 
              v-model="username"
              type="text" 
              autocomplete="username"
              class="w-full h-10 px-3 rounded-md border border-input bg-background text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Enter your username"
            >
          </div>
          
          <div class="space-y-2">
            <label class="text-sm font-medium">Password</label>
            <div class="relative">
              <input 
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                class="w-full h-10 px-3 pr-10 rounded-md border border-input bg-background text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                placeholder="Enter your password"
              >
              <button 
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <Eye v-if="!showPassword" class="h-4 w-4" />
                <EyeOff v-else class="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <div v-if="error" class="text-sm text-red-500 text-center">
            {{ error }}
          </div>
          
          <Button type="submit" class="w-full" :disabled="loading">
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign In</span>
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
