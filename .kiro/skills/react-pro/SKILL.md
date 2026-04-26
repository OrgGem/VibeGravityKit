---
name: react-pro
description: "Expert React development — hooks, performance optimization, state management patterns, and modern React 18+ features. Use for building scalable React applications and components."
user-invocable: true
risk: safe
---

# React Pro

Expert React developer — modern hooks, performance patterns, and scalable component architecture with React 18+.

## When to Use
- Building complex React components with advanced hooks
- Optimizing React rendering performance
- Implementing state management patterns
- Working with React 18 concurrent features (Suspense, transitions)
- Code review for React best practices

## Core Patterns

### Custom Hooks
```tsx
// Encapsulate logic into reusable hooks
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      return JSON.parse(localStorage.getItem(key) ?? '') ?? initial
    } catch {
      return initial
    }
  })
  const set = useCallback((v: T) => {
    setValue(v)
    localStorage.setItem(key, JSON.stringify(v))
  }, [key])
  return [value, set] as const
}
```

### Performance Optimization
```tsx
// Memoize expensive computations
const sorted = useMemo(() => items.sort(compareFn), [items])

// Stable callback references
const handleClick = useCallback((id: string) => {
  dispatch({ type: 'select', id })
}, [dispatch])

// Prevent unnecessary re-renders
const Row = memo(({ item, onSelect }: Props) => (
  <tr onClick={() => onSelect(item.id)}>{item.name}</tr>
))

// Virtualize long lists
import { useVirtualizer } from '@tanstack/react-virtual'
```

### Context Pattern (avoid prop drilling)
```tsx
interface AuthContext {
  user: User | null
  logout: () => void
}

const AuthCtx = createContext<AuthContext | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const logout = useCallback(() => setUser(null), [])
  return <AuthCtx.Provider value={{ user, logout }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
```

### React 18 Concurrent Features
```tsx
// Transitions for non-urgent updates
const [isPending, startTransition] = useTransition()
startTransition(() => setSearchQuery(input))  // Doesn't block typing

// Deferred value for expensive derived state
const deferred = useDeferredValue(searchQuery)
const results = useMemo(() => filter(items, deferred), [items, deferred])

// Suspense for async data
function UserProfile({ userId }: { userId: string }) {
  const user = use(fetchUser(userId))  // React 19 use()
  return <div>{user.name}</div>
}

<Suspense fallback={<Skeleton />}>
  <UserProfile userId={id} />
</Suspense>
```

### Error Boundaries
```tsx
'use client'  // Next.js: error.tsx must be client
import { Component, ErrorInfo } from 'react'

class ErrorBoundary extends Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack)
  }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children
  }
}
```

### Form Handling (React Hook Form + Zod)
```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})
type FormData = z.infer<typeof schema>

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema)
  })
  const onSubmit = (data: FormData) => console.log(data)
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <p>{errors.email.message}</p>}
    </form>
  )
}
```

## Best Practices
- Lift state to the lowest common ancestor, not higher
- Prefer composition over prop drilling — use render props or children
- Keep components under 150 lines — extract custom hooks for logic
- Never mutate state directly — always return new objects/arrays
- Cleanup effects: return cleanup function from useEffect
- Use `key` prop correctly — stable ID, never array index for dynamic lists
