---
name: graphql-schema-design
description: "GraphQL schema design best practices — types, queries, mutations, subscriptions, Relay pagination, and federation. Use when designing or reviewing GraphQL APIs."
user-invocable: true
risk: safe
---

# GraphQL Schema Design

Expert GraphQL schema architect — scalable, maintainable, and performant GraphQL API design.

## When to Use
- Designing a new GraphQL schema from scratch
- Reviewing or refactoring existing GraphQL types
- Implementing pagination, filtering, or sorting patterns
- Designing mutations with proper error handling
- Planning GraphQL federation across microservices

## Core Type Design

```graphql
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
  email: String!
  posts(first: Int, after: String): PostConnection!
  createdAt: DateTime!
}

scalar DateTime
scalar URL
scalar Email
```

## Relay Cursor Pagination

```graphql
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  posts(first: Int, after: String, last: Int, before: String): PostConnection!
}
```

## Mutation Error Pattern (Union)

```graphql
type CreateUserSuccess { user: User! }
type ValidationError { field: String!; message: String! }
type DuplicateEmailError { email: String! }

union CreateUserResult = CreateUserSuccess | ValidationError | DuplicateEmailError

input CreateUserInput {
  name: String!
  email: String!
  role: UserRole = VIEWER
}

enum UserRole { ADMIN EDITOR VIEWER }

type Mutation {
  createUser(input: CreateUserInput!): CreateUserResult!
}
```

## Subscriptions

```graphql
type Subscription {
  messageAdded(channelId: ID!): Message!
  orderStatusChanged(orderId: ID!): Order!
}
```

## Naming Conventions
- Types: `PascalCase` — `UserProfile`, `OrderItem`
- Fields: `camelCase` — `firstName`, `createdAt`
- Enums: `SCREAMING_SNAKE_CASE` — `ACTIVE_USER`
- Mutations: verb + noun — `createUser`, `updatePost`, `deleteComment`
- Queries: noun, plural for lists — `users`, `post(id:)`

## Schema Design Rules
- Never return `null` for list fields — return `[]`
- Use `!` (non-null) for guaranteed data, nullable for optional
- Use `ID!` for all entity identifiers
- Group related args into Input types, not individual scalars
- Deprecate before removing: `@deprecated(reason: "Use newField instead")`
- Never use generic `JSON` scalar for structured data — define explicit types

## Performance
- Use DataLoader for all relationship resolvers (prevents N+1)
- Add query complexity limits for public APIs
- Use persisted queries in production
- Implement query depth limiting
