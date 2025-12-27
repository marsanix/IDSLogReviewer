<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Activity, User, LogIn, LogOut, Eye } from 'lucide-vue-next'
import axios from 'axios'

interface ActivityData {
  id: number
  username: string
  action: string
  page: string | null
  details: string | null
  ip_address: string
  timestamp: string
}

const activities = ref<ActivityData[]>([])
const loading = ref(false)

const actionIcons: Record<string, any> = {
  'login': LogIn,
  'logout': LogOut,
  'login_failed': LogIn,
  'default': Eye
}

function getActionIcon(action: string) {
  return actionIcons[action] || actionIcons.default
}

function getActionColor(action: string) {
  if (action === 'login') return 'text-green-500'
  if (action === 'logout') return 'text-yellow-500'
  if (action === 'login_failed') return 'text-red-500'
  return 'text-muted-foreground'
}

async function fetchActivities() {
  loading.value = true
  try {
    const res = await axios.get('/api/activity?limit=200')
    activities.value = res.data.activities
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchActivities)
</script>

<template>
  <div class="space-y-6">
    <Card class="h-full flex flex-col">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Activity class="h-5 w-5" />
          Activity Logs
        </CardTitle>
      </CardHeader>
      <CardContent class="flex-1 overflow-auto">
        <div v-if="loading" class="h-1 w-full bg-secondary overflow-hidden mb-4">
          <div class="h-full bg-primary animate-progress origin-left-right"></div>
        </div>
        
        <div class="relative w-full overflow-auto">
          <table class="w-full caption-bottom text-sm">
            <thead>
              <tr class="border-b">
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Time</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">User</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Action</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Details</th>
                <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">IP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="activity in activities" :key="activity.id" class="border-b hover:bg-muted/50">
                <td class="p-4 align-middle whitespace-nowrap text-muted-foreground">
                  {{ new Date(activity.timestamp).toLocaleString() }}
                </td>
                <td class="p-4 align-middle">
                  <div class="flex items-center gap-2">
                    <User class="h-4 w-4 text-muted-foreground" />
                    {{ activity.username || 'anonymous' }}
                  </div>
                </td>
                <td class="p-4 align-middle">
                  <div class="flex items-center gap-2" :class="getActionColor(activity.action)">
                    <component :is="getActionIcon(activity.action)" class="h-4 w-4" />
                    <span class="capitalize">{{ activity.action.replace('_', ' ') }}</span>
                  </div>
                </td>
                <td class="p-4 align-middle text-muted-foreground">
                  {{ activity.details || activity.page || '-' }}
                </td>
                <td class="p-4 align-middle font-mono text-xs text-muted-foreground">
                  {{ activity.ip_address }}
                </td>
              </tr>
              <tr v-if="activities.length === 0 && !loading">
                <td colspan="5" class="p-4 text-center text-muted-foreground">No activity logs found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
