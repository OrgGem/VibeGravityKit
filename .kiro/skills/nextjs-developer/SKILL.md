---
name: nextjs-developer
description: "Full-stack Next.js development with App Router, Server Components, Server Actions, and modern patterns. Use for building Next.js applications, APIs, and optimizing performance."
user-invocable: true
risk: safe
---

# Next.js Developer

Expert Next.js full-stack developer — App Router, Server Components, streaming, and production-ready patterns.

## When to Use
- Building pages and layouts with Next.js App Router
- Implementing Server Components and Client Components correctly
- Creating API routes and Server Actions
- Optimizing images, fonts, and Core Web Vitals
- Configuring Next.js for deployment (Vercel, Docker, self-hosted)

## App Router Fundamentals

### File Conventions
```
app/
├── layout.tsx          # Root layout (always Server Component)
├── page.tsx            # Route page
├── loading.tsx         # Suspense fallback
├── error.tsx           # Error boundary ('use client')
├── not-found.tsx       # 404 page
├── (auth)/             # Route group (no URL segment)
│   ├── login/page.tsx
│   └── register/page.tsx
├── blog/
│   ├── [slug]/page.tsx # Dynamic segment
│   └── [...rest]/      # Catch-all segment
└── api/route.ts        # Route Handler
```

### Server vs Client Components
```tsx
// Server Component (default) — runs on server, no hooks, no browser APIs
async function UserProfile({ id }: { id: string }) {
  const user = await db.user.findUnique({ where: { id } })
  return <div>{user.name}</div>
}

// Client Component — interactive, uses hooks
'use client'
import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}
```

### Data Fetching
```tsx
// Server Component — direct async/await
async function Page() {
  // Deduped and cached automatically
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 }  // ISR: revalidate every hour
  })
  const json = await data.json()
  return <div>{json.title}</div>
}

// With Suspense streaming
export default function Page() {
  return (
    <Suspense fallback={<Skeleton />}>
      <SlowComponent />
    </Suspense>
  )
}
```

### Server Actions
```tsx
// app/actions.ts
'use server'
import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  await db.post.create({ data: { title } })
  revalidatePath('/posts')
}

// Usage in component
<form action={createPost}>
  <input name="title" />
  <button type="submit">Create</button>
</form>
```

### Route Handlers
```ts
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  const users = await db.user.findMany()
  return NextResponse.json(users)
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const user = await db.user.create({ data: body })
  return NextResponse.json(user, { status: 201 })
}
```

### Metadata
```tsx
// app/blog/[slug]/page.tsx
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost(params.slug)
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: { images: [post.coverImage] }
  }
}
```

## Performance Patterns
- Use `next/image` for automatic optimization (WebP, lazy loading, LQIP)
- Use `next/font` to eliminate layout shift from custom fonts
- Prefer Server Components — they don't add to JS bundle
- Use `Suspense` boundaries to stream heavy sections
- Enable PPR (Partial Prerendering) for static + dynamic hybrid pages

## Best Practices
- Keep Client Components as leaf nodes — push interactivity down
- Use `use server` for form mutations, `use client` only when needed
- Validate Server Action inputs with Zod before DB writes
- Use `unstable_cache` for fine-grained caching control
- Co-locate route handlers with their feature folder
