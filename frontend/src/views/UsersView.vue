<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { UserPlus, Trash2, Shield, User } from 'lucide-vue-next'
import axios from 'axios'

interface UserData {
  id: number
  username: string
  role: string
  created_at: string
}

const users = ref<UserData[]>([])
const loading = ref(false)
const showCreateForm = ref(false)
const newUsername = ref('')
const newPassword = ref('')
const newRole = ref('viewer')
const error = ref('')

async function fetchUsers() {
  loading.value = true
  try {
    const res = await axios.get('/api/users')
    users.value = res.data.users
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Failed to fetch users'
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!newUsername.value.trim() || !newPassword.value) {
    error.value = 'Username and password required'
    return
  }
  
  try {
    await axios.post('/api/users', {
      username: newUsername.value.trim(),
      password: newPassword.value,
      role: newRole.value
    })
    newUsername.value = ''
    newPassword.value = ''
    newRole.value = 'viewer'
    showCreateForm.value = false
    error.value = ''
    fetchUsers()
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Failed to create user'
  }
}

async function deleteUser(userId: number) {
  if (!confirm('Are you sure you want to delete this user?')) return
  
  try {
    await axios.delete(`/api/users/${userId}`)
    fetchUsers()
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Failed to delete user'
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="space-y-6">
    <Card>
      <CardHeader class="flex flex-row items-center justify-between">
        <CardTitle class="flex items-center gap-2">
          <Shield class="h-5 w-5" />
          Users Management
        </CardTitle>
        <Button @click="showCreateForm = !showCreateForm" size="sm">
          <UserPlus class="h-4 w-4 mr-2" />
          Add User
        </Button>
      </CardHeader>
      <CardContent>
        <!-- Create User Form -->
        <div v-if="showCreateForm" class="mb-6 p-4 border rounded-lg space-y-4">
          <h3 class="font-medium">Create New User</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <input 
              v-model="newUsername"
              type="text"
              placeholder="Username"
              class="h-9 px-3 rounded-md border border-input bg-background text-sm"
            >
            <input 
              v-model="newPassword"
              type="password"
              placeholder="Password"
              class="h-9 px-3 rounded-md border border-input bg-background text-sm"
            >
            <select 
              v-model="newRole"
              class="h-9 px-3 rounded-md border border-input bg-background text-sm"
            >
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="flex gap-2">
            <Button @click="createUser" size="sm">Create</Button>
            <Button @click="showCreateForm = false" variant="outline" size="sm">Cancel</Button>
          </div>
        </div>
        
        <div v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</div>
        
        <!-- Users Table -->
        <div class="relative w-full overflow-auto">
          <table class="w-full caption-bottom text-sm">
            <thead>
              <tr class="border-b">
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">User</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Role</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Created</th>
                <th class="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id" class="border-b hover:bg-muted/50">
                <td class="p-4 align-middle">
                  <div class="flex items-center gap-2">
                    <User class="h-4 w-4 text-muted-foreground" />
                    {{ user.username }}
                  </div>
                </td>
                <td class="p-4 align-middle">
                  <span 
                    class="px-2 py-0.5 rounded text-xs font-medium capitalize"
                    :class="user.role === 'admin' ? 'bg-primary/10 text-primary' : 'bg-secondary text-secondary-foreground'"
                  >
                    {{ user.role }}
                  </span>
                </td>
                <td class="p-4 align-middle text-muted-foreground">
                  {{ new Date(user.created_at).toLocaleDateString() }}
                </td>
                <td class="p-4 align-middle text-right">
                  <Button 
                    variant="ghost" 
                    size="icon"
                    class="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-500/10"
                    @click="deleteUser(user.id)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </td>
              </tr>
              <tr v-if="users.length === 0 && !loading">
                <td colspan="4" class="p-4 text-center text-muted-foreground">No users found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
