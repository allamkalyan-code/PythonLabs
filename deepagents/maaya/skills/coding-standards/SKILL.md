---
name: coding-standards
description: "Stack-specific coding patterns and examples for FastAPI, SQLAlchemy,
  React, Pydantic, pytest, and Vitest. Read this before writing any code."
---

# Coding Standards Skill

Read this skill before writing any code. Follow every pattern exactly —
consistency across agents is more important than personal style preferences.

---

## FastAPI Route Pattern

Always split into three layers: **router** (HTTP), **service** (business logic), **schema** (validation).
Never put business logic in the router function.

```python
# backend/app/routers/items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.requests import CreateItemRequest
from app.schemas.responses import ItemResponse
from app.services.item_service import create_item, get_item_by_id

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item_route(
    payload: CreateItemRequest,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Create a new item. Returns 409 if title already exists."""
    existing = await get_item_by_id(db, title=payload.title)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Item with this title already exists", "code": "ITEM_EXISTS"},
        )
    item = await create_item(db, payload)
    return ItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item_route(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Get an item by ID. Returns 404 if not found."""
    item = await get_item_by_id(db, item_id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Item not found", "code": "ITEM_NOT_FOUND"},
        )
    return ItemResponse.model_validate(item)
```

```python
# backend/app/services/item_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.schemas.requests import CreateItemRequest


async def create_item(db: AsyncSession, payload: CreateItemRequest) -> Item:
    item = Item(title=payload.title, description=payload.description)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_item_by_id(db: AsyncSession, *, item_id: int | None = None, title: str | None = None) -> Item | None:
    if item_id is not None:
        result = await db.execute(select(Item).where(Item.id == item_id))
    elif title is not None:
        result = await db.execute(select(Item).where(Item.title == title))
    else:
        return None
    return result.scalar_one_or_none()
```

---

## Pydantic Schema Pattern

Always separate request and response schemas. Never reuse the same model for both.

```python
# backend/app/schemas/requests.py
from pydantic import BaseModel, Field


class CreateItemRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class UpdateItemRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
```

```python
# backend/app/schemas/responses.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # enables .model_validate(orm_object)

    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
```

---

## SQLAlchemy Model Pattern

Use `Mapped` and `mapped_column` (SQLAlchemy 2.0 syntax). Always include `created_at` and `updated_at`.

```python
# backend/app/models/item.py
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Item id={self.id} title={self.title!r}>"
```

---

## React Component Pattern

One component per file. Explicit prop interface. No inline styles — Tailwind only.

```tsx
// frontend/src/components/items/ItemCard.tsx
import { useState } from 'react'
import type { Item } from '@/types'

interface ItemCardProps {
  item: Item
  onDelete: (id: number) => void
  isLoading?: boolean
}

export function ItemCard({ item, onDelete, isLoading = false }: ItemCardProps) {
  const [isConfirming, setIsConfirming] = useState(false)

  const handleDelete = () => {
    if (!isConfirming) {
      setIsConfirming(true)
      return
    }
    onDelete(item.id)
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-gray-900">{item.title}</h3>
      {item.description && (
        <p className="mt-1 text-sm text-gray-500">{item.description}</p>
      )}
      <button
        onClick={handleDelete}
        disabled={isLoading}
        className="mt-3 text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
      >
        {isConfirming ? 'Confirm delete?' : 'Delete'}
      </button>
    </div>
  )
}
```

```tsx
// frontend/src/types/index.ts  — co-locate types with their domain
export interface Item {
  id: number
  title: string
  description: string | null
  isActive: boolean
  createdAt: string
  updatedAt: string
}
```

---

## pytest Pattern

Use fixtures for setup. One `assert` per logical check (or group related asserts clearly).
Mock all external services. Use `pytest.mark.parametrize` for edge cases.

```python
# tests/test_items.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


@pytest.fixture
async def sample_item(db: AsyncSession) -> Item:
    """Create a test item directly in DB — bypasses the API."""
    item = Item(title="Test Item", description="A fixture item")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def test_create_item_returns_201(client: AsyncClient) -> None:
    response = await client.post("/items/", json={"title": "New Item"})

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Item"
    assert "id" in data


async def test_create_item_duplicate_returns_409(
    client: AsyncClient, sample_item: Item
) -> None:
    response = await client.post("/items/", json={"title": sample_item.title})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ITEM_EXISTS"


async def test_get_item_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get("/items/99999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ITEM_NOT_FOUND"


@pytest.mark.parametrize("title", ["", " ", "a" * 201])
async def test_create_item_invalid_title_returns_422(
    client: AsyncClient, title: str
) -> None:
    response = await client.post("/items/", json={"title": title})
    assert response.status_code == 422
```

---

## Vitest Pattern

Use `describe` to group, `it` for individual cases. Mock API calls with `vi.fn()`.
Use `@testing-library/react` for component tests — query by role, not by class.

```typescript
// frontend/src/__tests__/ItemCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ItemCard } from '@/components/items/ItemCard'
import type { Item } from '@/types'

const mockItem: Item = {
  id: 1,
  title: 'Test Item',
  description: 'A description',
  isActive: true,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
}

describe('ItemCard', () => {
  it('renders item title and description', () => {
    render(<ItemCard item={mockItem} onDelete={vi.fn()} />)

    expect(screen.getByText('Test Item')).toBeInTheDocument()
    expect(screen.getByText('A description')).toBeInTheDocument()
  })

  it('calls onDelete with item id after confirmation', () => {
    const onDelete = vi.fn()
    render(<ItemCard item={mockItem} onDelete={onDelete} />)

    fireEvent.click(screen.getByText('Delete'))
    expect(onDelete).not.toHaveBeenCalled() // first click = confirm prompt

    fireEvent.click(screen.getByText('Confirm delete?'))
    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('disables delete button when isLoading is true', () => {
    render(<ItemCard item={mockItem} onDelete={vi.fn()} isLoading />)

    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

---

## Quick Reference Checklist

Before submitting any code, verify:

- [ ] Function names are `snake_case` (Python) or `camelCase` (TS)
- [ ] Boolean variables start with `is_`, `has_`, or `can_`
- [ ] No function exceeds 30 lines
- [ ] No nesting deeper than 3 levels
- [ ] Every `except` catches a specific exception type
- [ ] Every FastAPI endpoint has a request schema and a response schema
- [ ] Error responses use `{"detail": "...", "code": "..."}` shape
- [ ] Every new function has at least one test
- [ ] No `TODO` left without `# TECH DEBT:` annotation and date
