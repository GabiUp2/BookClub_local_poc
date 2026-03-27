# ADR-002: Database Interface Layer Design

**Status:** Accepted
**Date:** 2026-03-27
**Deciders:** Bartosz Wichowski
**Depends on:** ADR-001 (PostgreSQL + pgvector)

## Context

Per ADR-001, BookClub will use PostgreSQL + pgvector as its unified storage layer, but with a phased approach: starting with in-memory/numpy vectors (boot.dev course alignment), then migrating to pgvector. Additionally, the free desktop tier may eventually need to support SQLite for zero-dependency offline use.

This means the application code must not be coupled to any specific database implementation. We need an interface (port) that defines what the storage layer must do, with swappable implementations (adapters).

This is also a learning exercise: implementing the Ports & Adapters (Hexagonal Architecture) pattern explicitly, understanding why it exists and where it helps.

## Decision

Define Python Protocol classes (abstract interfaces) for all storage operations. Provide concrete implementations that can be swapped via configuration.

### Why Protocols over ABC

Python's `typing.Protocol` (PEP 544) provides structural subtyping — an implementation satisfies the interface if it has the right methods, without needing to inherit from a base class. This is:
- More Pythonic (duck typing with type safety)
- Easier to test (any object with matching methods works)
- No import dependency between interface and implementation

But ABCs (`abc.ABC`) are also valid and more explicit about intent. **Tradeoff to understand:** Protocol = structural ("if it walks like a duck"), ABC = nominal ("it must declare itself a duck"). For this project, Protocol is cleaner because implementations live in separate modules and shouldn't need to import the interface definition.

## Interface Specification

### Domain Models (Pydantic)

These are shared across all implementations. They define the data shapes, not the storage logic.

```python
# src/book_club/domain/models.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import uuid

class Book(BaseModel):
    id: uuid.UUID
    title: str
    file_path: str      # original PDF location
    file_hash: str       # content hash for dedup detection
    total_pages: int
    created_at: datetime

class Chunk(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    text: str
    page_start: int
    page_end: int
    section_heading: str | None = None  # if heading-aware chunking
    chunk_index: int     # position within book
    content_hash: str    # for dedup

class CardType(str, Enum):
    BASIC = "basic"
    CLOZE = "cloze"

class Card(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    source_chunk_id: uuid.UUID
    card_type: CardType
    question: str
    answer: str
    # SRS fields (SM-2 or FSRS — keep generic for now)
    easiness_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    due_date: datetime
    created_at: datetime

class ReviewResult(BaseModel):
    card_id: uuid.UUID
    quality: int          # 0-5 for SM-2, may change for FSRS
    reviewed_at: datetime

class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    chunk_text: str
    score: float          # similarity score
    page_start: int
    page_end: int
    book_id: uuid.UUID
```

### Storage Protocols (Interfaces)

```python
# src/book_club/domain/ports.py
from typing import Protocol, Sequence
import uuid
import numpy as np
from .models import Book, Chunk, Card, ReviewResult, SearchResult

class BookRepository(Protocol):
    """Manages book records."""

    async def save(self, book: Book) -> Book: ...
    async def get_by_id(self, book_id: uuid.UUID) -> Book | None: ...
    async def get_by_hash(self, file_hash: str) -> Book | None: ...
    async def list_all(self) -> Sequence[Book]: ...
    async def delete(self, book_id: uuid.UUID) -> bool: ...


class ChunkRepository(Protocol):
    """Manages text chunks and their metadata."""

    async def save_batch(self, chunks: Sequence[Chunk]) -> Sequence[Chunk]: ...
    async def get_by_book(self, book_id: uuid.UUID) -> Sequence[Chunk]: ...
    async def get_by_id(self, chunk_id: uuid.UUID) -> Chunk | None: ...
    async def delete_by_book(self, book_id: uuid.UUID) -> int: ...


class VectorStore(Protocol):
    """Manages vector embeddings and similarity search.

    This is deliberately separate from ChunkRepository.
    The chunk repo stores text + metadata.
    The vector store stores embeddings + does similarity search.

    Why separate: In Phase 1 (boot.dev approach), VectorStore
    is an in-memory numpy implementation. In Phase 2, it moves
    to pgvector. ChunkRepository stays PostgreSQL throughout.
    Keeping them separate means Phase 1→2 migration only
    touches VectorStore, not ChunkRepository.
    """

    async def upsert_embeddings(
        self, chunk_ids: Sequence[uuid.UUID], embeddings: np.ndarray
    ) -> None: ...

    async def search(
        self, query_embedding: np.ndarray, top_k: int = 5, book_id: uuid.UUID | None = None
    ) -> Sequence[SearchResult]: ...

    async def delete_by_book(self, book_id: uuid.UUID) -> int: ...


class CardRepository(Protocol):
    """Manages flashcards."""

    async def save_batch(self, cards: Sequence[Card]) -> Sequence[Card]: ...
    async def get_by_book(self, book_id: uuid.UUID) -> Sequence[Card]: ...
    async def get_due(self, limit: int = 10) -> Sequence[Card]: ...
    async def update(self, card: Card) -> Card: ...
    async def delete_by_book(self, book_id: uuid.UUID) -> int: ...


class ReviewRepository(Protocol):
    """Manages SRS review history."""

    async def save(self, result: ReviewResult) -> ReviewResult: ...
    async def get_by_card(self, card_id: uuid.UUID) -> Sequence[ReviewResult]: ...
    async def get_stats(self, since: datetime) -> dict: ...
```

### Implementation Plan (Phased)

```
Phase 1 (boot.dev aligned):
├── InMemoryVectorStore     ← numpy arrays, cosine similarity (boot.dev approach)
├── PostgresBookRepository  ← real persistence from day one
├── PostgresChunkRepository ← real persistence from day one
├── PostgresCardRepository  ← real persistence from day one
└── PostgresReviewRepository

Phase 2 (pgvector migration):
├── PgVectorStore           ← replaces InMemoryVectorStore
├── PostgresBookRepository  ← unchanged
├── PostgresChunkRepository ← unchanged
├── PostgresCardRepository  ← unchanged
└── PostgresReviewRepository

Phase 3 (hypothetical offline/SQLite):
├── InMemoryVectorStore     ← same as Phase 1
├── SQLiteBookRepository    ← lightweight alternative
├── SQLiteChunkRepository
├── SQLiteCardRepository
└── SQLiteReviewRepository
```

### Dependency Injection / Wiring

```python
# src/book_club/dependencies.py
"""
Wire up implementations based on configuration.
Keep this simple — no DI framework needed.
"""

from .domain.ports import BookRepository, ChunkRepository, VectorStore, CardRepository, ReviewRepository

def create_repositories(config) -> dict:
    """
    Factory that returns the right implementations
    based on config (e.g., APP_STORAGE_BACKEND=postgres|sqlite|memory).

    Returns a dict or a dataclass with all repos.
    The FastAPI app uses Depends() to inject these.
    """
    if config.storage_backend == "postgres":
        # import and instantiate PostgreSQL implementations
        ...
    elif config.storage_backend == "memory":
        # import and instantiate in-memory implementations (for testing)
        ...
    # etc.
```

### File Structure

```
src/book_club/
├── domain/
│   ├── __init__.py
│   ├── models.py          ← Pydantic models (Book, Chunk, Card, etc.)
│   └── ports.py           ← Protocol interfaces
├── adapters/
│   ├── __init__.py
│   ├── postgres/
│   │   ├── __init__.py
│   │   ├── connection.py  ← connection pool setup (asyncpg)
│   │   ├── books.py       ← PostgresBookRepository
│   │   ├── chunks.py      ← PostgresChunkRepository
│   │   ├── vectors.py     ← PgVectorStore (Phase 2)
│   │   ├── cards.py       ← PostgresCardRepository
│   │   ├── reviews.py     ← PostgresReviewRepository
│   │   └── migrations/    ← alembic migrations
│   ├── memory/
│   │   ├── __init__.py
│   │   └── vectors.py     ← InMemoryVectorStore (Phase 1, numpy)
│   └── embedding/
│       ├── __init__.py
│       ├── base.py        ← EmbeddingProvider protocol
│       ├── sentence_transformers.py  ← local (all-MiniLM-L6-v2)
│       └── openai.py      ← remote (text-embedding-3-small)
├── dependencies.py        ← Factory / wiring
└── preprocessing_server/
    └── server_main.py     ← FastAPI app (uses injected repos)
```

## Consequences

**What becomes easier:**
- Swapping vector backends is a config change, not a rewrite
- Testing: inject in-memory implementations, no Docker needed for unit tests
- Boot.dev → BookClub porting: numpy vector code maps 1:1 to InMemoryVectorStore
- Desktop vs. cloud packaging: choose implementations at startup

**What becomes harder:**
- More files, more indirection — but each file is small and focused
- Must maintain interface compatibility across implementations
- Async everywhere (but FastAPI wants this anyway)

**What to watch for:**
- Don't leak implementation details through the interface (e.g., no SQL in port definitions)
- Keep models in `domain/` — they belong to the business logic, not the storage layer
- The EmbeddingProvider is a separate protocol from VectorStore — embedding ≠ storage

## Design Rationale (Learning Notes)

**Why separate VectorStore from ChunkRepository?**
Chunks are text + metadata (relational data). Vectors are numeric arrays for similarity search. In Phase 1, chunks live in PostgreSQL while vectors live in numpy arrays. Merging them would force you to migrate both at once. Separating them means Phase 2 only changes one implementation.

**Why async?**
FastAPI is async-native. asyncpg (PostgreSQL driver) is significantly faster than synchronous alternatives for concurrent requests. And it teaches async patterns, which matter for the observability presentation (you can trace concurrent DB calls).

**Why not SQLAlchemy ORM?**
For a learning project, raw asyncpg or psycopg3 with explicit SQL teaches you more than hiding queries behind an ORM. You'll see exactly what queries hit the database, which feeds into observability (query tracing, EXPLAIN ANALYZE). If this becomes tedious later, SQLAlchemy can be added as another adapter — the interface doesn't change.

**Why Pydantic models and not dataclasses?**
Pydantic gives you validation, serialization, and JSON schema for free. FastAPI already depends on it. The models serve double duty: domain objects AND API response schemas.
