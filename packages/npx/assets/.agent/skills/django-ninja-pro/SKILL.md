---
name: django-ninja-pro
description: "Build high-performance Django APIs with Django Ninja — type-safe, async-ready, auto-documented. Use for REST API development with Django backends that need FastAPI-style ergonomics."
user-invocable: true
risk: safe
---

# Django Ninja Pro

Expert Django Ninja developer — FastAPI-style APIs built on Django's ORM, auth, and admin ecosystem.

## When to Use
- Building REST APIs with Django that need auto-generated OpenAPI docs
- Adding typed, validated endpoints to existing Django projects
- Async API views with Django ORM
- Replacing DRF with a modern, type-safe alternative

## Setup

```bash
pip install django-ninja
```

```python
# urls.py
from ninja import NinjaAPI
api = NinjaAPI()

urlpatterns = [
    path("api/", api.urls),
]
```

## Core Patterns

### Basic Endpoint with Schema
```python
from ninja import NinjaAPI, Schema
from pydantic import Field

api = NinjaAPI()

class UserIn(Schema):
    name: str = Field(..., min_length=1)
    email: str

class UserOut(Schema):
    id: int
    name: str
    email: str

@api.post("/users", response=UserOut)
def create_user(request, payload: UserIn):
    user = User.objects.create(**payload.dict())
    return user
```

### Authentication
```python
from ninja.security import HttpBearer

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            return Token.objects.get(key=token).user
        except Token.DoesNotExist:
            return None

@api.get("/me", auth=AuthBearer(), response=UserOut)
def get_me(request):
    return request.auth
```

### Async Views
```python
@api.get("/items", response=list[ItemOut])
async def list_items(request):
    items = await Item.objects.all().aiterator()
    return [item async for item in items]
```

### Router Organization
```python
# users/api.py
from ninja import Router
router = Router()

@router.get("/")
def list_users(request): ...

# main urls.py
api.add_router("/users/", "users.api.router")
```

### Pagination
```python
from ninja.pagination import paginate, PageNumberPagination

@api.get("/items", response=list[ItemOut])
@paginate(PageNumberPagination, page_size=20)
def list_items(request):
    return Item.objects.all()
```

## Best Practices
- Use `Schema` for all request/response types — enables automatic validation + docs
- Organize routes into `Router()` modules, not a single giant file
- Use Django's built-in auth (`request.user`) — Ninja integrates seamlessly
- Prefer async views for I/O-heavy endpoints
- Use `api.exception_handler` for consistent error responses
