---
name: vue-nuxt-developer
description: "Full-stack Vue 3 and Nuxt 3 development — Composition API, Pinia, server-side rendering, and auto-imports. Use for building Vue/Nuxt applications with modern patterns."
user-invocable: true
risk: safe
---

# Vue / Nuxt Developer

Expert Vue 3 and Nuxt 3 full-stack developer — Composition API, Pinia state management, SSR, and file-based routing.

## When to Use
- Building Vue 3 components with Composition API
- Full-stack Nuxt 3 applications with SSR/SSG
- State management with Pinia
- Server routes and API handlers in Nuxt
- Migrating from Vue 2 Options API to Vue 3 Composition API

## Vue 3 Composition API

### Component Structure
```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

interface Props {
  userId: string
}
const props = defineProps<Props>()
const emit = defineEmits<{ update: [user: User] }>()

const user = ref<User | null>(null)
const fullName = computed(() => `${user.value?.firstName} ${user.value?.lastName}`)

watch(() => props.userId, async (id) => {
  user.value = await fetchUser(id)
}, { immediate: true })

onMounted(() => console.log('mounted'))
</script>

<template>
  <div v-if="user">
    <h1>{{ fullName }}</h1>
    <button @click="emit('update', user)">Save</button>
  </div>
  <div v-else>Loading...</div>
</template>
```

### Composables (Custom Hooks)
```ts
// composables/useUser.ts
export function useUser(userId: Ref<string>) {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  watchEffect(async () => {
    loading.value = true
    try {
      user.value = await fetchUser(userId.value)
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  })

  return { user: readonly(user), loading: readonly(loading), error }
}
```

### Pinia Store
```ts
// stores/auth.ts
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!user.value)

  async function login(credentials: Credentials) {
    user.value = await authApi.login(credentials)
  }

  function logout() {
    user.value = null
  }

  return { user, isLoggedIn, login, logout }
})

// Usage
const auth = useAuthStore()
await auth.login({ email, password })
```

## Nuxt 3 Patterns

### File Structure
```
nuxt-app/
├── app.vue              # App root
├── pages/               # File-based routing
│   ├── index.vue        # /
│   ├── blog/
│   │   ├── index.vue    # /blog
│   │   └── [slug].vue   # /blog/:slug
├── components/          # Auto-imported
├── composables/         # Auto-imported
├── server/
│   ├── api/             # API routes
│   │   └── users.get.ts # GET /api/users
│   └── middleware/      # Server middleware
├── middleware/          # Route middleware
└── stores/              # Pinia stores
```

### Data Fetching
```vue
<script setup lang="ts">
// SSR-aware composables
const { data: posts, pending, error } = await useFetch('/api/posts')

// With reactivity
const page = ref(1)
const { data } = await useFetch('/api/posts', {
  query: { page },  // Refetches on page change
  transform: (data) => data.items
})

// Server-only fetch
const { data } = await useAsyncData('posts', () => $fetch('/api/posts'))
</script>
```

### Server API Routes
```ts
// server/api/users/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const user = await db.user.findUnique({ where: { id } })
  if (!user) throw createError({ statusCode: 404, message: 'User not found' })
  return user
})

// server/api/users/index.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return db.user.create({ data: body })
})
```

### Middleware
```ts
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn && to.path !== '/login') {
    return navigateTo('/login')
  }
})
```

## Best Practices
- Use `<script setup>` — it's the idiomatic Vue 3 way
- Keep composables small and single-purpose
- Use `readonly()` when returning reactive state from composables
- Prefer `useFetch` over `$fetch` in components (SSR-safe, deduped)
- Use Pinia over Vuex — simpler, TypeScript-native, Devtools support
- Extract repeated server logic into `server/utils/` helpers
