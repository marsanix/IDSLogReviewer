<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LogOut, Moon, Sun, Monitor } from 'lucide-vue-next'

const emit = defineEmits(['logout'])

type Theme = 'light' | 'dark' | 'system'
const theme = ref<Theme>('system')

function setTheme(newTheme: Theme) {
  theme.value = newTheme
  localStorage.setItem('theme', newTheme)
  applyTheme(newTheme)
}

function applyTheme(t: Theme) {
  const root = document.documentElement
  
  if (t === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
  } else if (t === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

function handleLogout() {
  emit('logout')
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme') as Theme | null
  if (savedTheme) {
    theme.value = savedTheme
    applyTheme(savedTheme)
  }
})
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <Card>
      <CardHeader>
        <CardTitle>System Settings</CardTitle>
      </CardHeader>
      <CardContent class="space-y-6">

        <div class="flex items-center justify-between p-4 border rounded-lg">
           <div class="space-y-0.5">
            <div class="text-base font-medium">Theme Preferences</div>
            <div class="text-sm text-muted-foreground">
              Choose your preferred color scheme.
            </div>
          </div>
          <div class="flex gap-1">
            <Button 
              :variant="theme === 'light' ? 'default' : 'outline'" 
              size="icon"
              class="h-9 w-9"
              @click="setTheme('light')"
            >
              <Sun class="h-4 w-4" />
            </Button>
            <Button 
              :variant="theme === 'dark' ? 'default' : 'outline'" 
              size="icon"
              class="h-9 w-9"
              @click="setTheme('dark')"
            >
              <Moon class="h-4 w-4" />
            </Button>
            <Button 
              :variant="theme === 'system' ? 'default' : 'outline'" 
              size="icon"
              class="h-9 w-9"
              @click="setTheme('system')"
            >
              <Monitor class="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div class="flex items-center justify-between p-4 border rounded-lg border-red-500/20">
           <div class="space-y-0.5">
            <div class="text-base font-medium">Sign Out</div>
            <div class="text-sm text-muted-foreground">
              End your session and return to the login page.
            </div>
          </div>
          <Button variant="destructive" @click="handleLogout">
            <LogOut class="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>

      </CardContent>
    </Card>
  </div>
</template>
