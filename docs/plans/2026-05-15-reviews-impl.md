# Reviews & Star Ratings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use godmode:task-runner to implement this plan task-by-task.

**Goal:** Add a per-keg review system (name + 1–5 stars + optional comment) visible on the public display page, with admin delete capability.

**Architecture:** New `Review` SQLAlchemy model persisted in SQLite. Three new API endpoints in `routers/reviews.py`. `KegOut` gains `avg_stars`/`review_count` computed fields populated by a single aggregate query. Frontend adds `StarRating.svelte` and a collapsible review panel inside `KegCard.svelte`.

**Tech Stack:** Python 3 / FastAPI / SQLAlchemy / SQLite (backend); Svelte 4 / SvelteKit static (frontend); pytest / vitest (tests).

---

### Task 1: Add Review model

**Files:**
- Modify: `api/models.py`

**Step 1: Add the Review class**

Add after the `Stat` class in `api/models.py`:

```python
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keg_id = Column(Integer, nullable=False)
    name = Column(Text, nullable=False)
    stars = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
```

No FK constraint (`ForeignKey("kegs.id")`) — SQLite FK enforcement is off by default and the keg rows are permanent, so the simple integer reference is safe here.

**Step 2: Verify the model imports cleanly**

Run from `api/`:
```bash
python -c "from models import Review; print(Review.__tablename__)"
```
Expected output: `reviews`

**Step 3: Commit**

```bash
git add api/models.py
git commit -m "feat: add Review SQLAlchemy model"
```

---

### Task 2: Add Review schemas and update KegOut

**Files:**
- Modify: `api/schemas.py`

**Step 1: Add ReviewCreate and ReviewOut, extend KegOut**

In `api/schemas.py`, add after the `LoginIn` class:

```python
class ReviewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    stars: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: int
    keg_id: int
    name: str
    stars: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

Also add `field_validator` to the imports at the top:
```python
from pydantic import BaseModel, Field, HttpUrl, field_validator
```

Replace the existing `KegOut` class with:
```python
class KegOut(KegBase):
    id: int
    created_at: datetime
    updated_at: datetime
    avg_stars: Optional[float] = None
    review_count: int = 0
```

**Step 2: Verify schemas load**

```bash
cd api && python -c "from schemas import ReviewCreate, ReviewOut, KegOut; print('ok')"
```
Expected: `ok`

**Step 3: Commit**

```bash
git add api/schemas.py
git commit -m "feat: add ReviewCreate/ReviewOut schemas, extend KegOut with avg_stars"
```

---

### Task 3: Create reviews router with tests (TDD)

**Files:**
- Create: `api/routers/reviews.py`
- Create: `api/tests/test_reviews_api.py`

**Step 1: Write the failing tests first**

Create `api/tests/test_reviews_api.py`:

```python
import os
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_EXPIRE_HOURS", "1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def get_token():
    from auth import create_access_token
    return create_access_token({"sub": "admin"})

def first_keg_id():
    return client.get("/api/kegs").json()[0]["id"]


def test_list_reviews_empty():
    keg_id = first_keg_id()
    r = client.get(f"/api/kegs/{keg_id}/reviews")
    assert r.status_code == 200
    assert r.json() == []


def test_post_review_minimal():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 5})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["stars"] == 5
    assert data["comment"] is None
    assert data["keg_id"] == keg_id


def test_post_review_with_comment():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews",
                    json={"name": "Bob", "stars": 4, "comment": "Lovely malt!"})
    assert r.status_code == 201
    assert r.json()["comment"] == "Lovely malt!"


def test_post_review_name_is_stripped():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "  Alice  ", "stars": 3})
    assert r.status_code == 201
    assert r.json()["name"] == "Alice"


def test_post_review_stars_out_of_range():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 6})
    assert r.status_code == 422

    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 0})
    assert r.status_code == 422


def test_post_review_empty_name():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "   ", "stars": 3})
    assert r.status_code == 422


def test_post_review_comment_too_long():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews",
                    json={"name": "Alice", "stars": 3, "comment": "x" * 501})
    assert r.status_code == 422


def test_list_reviews_newest_first():
    keg_id = first_keg_id()
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 5})
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Bob", "stars": 2})
    reviews = client.get(f"/api/kegs/{keg_id}/reviews").json()
    assert len(reviews) == 2
    assert reviews[0]["name"] == "Bob"  # newest first


def test_delete_review_requires_auth():
    keg_id = first_keg_id()
    review_id = client.post(f"/api/kegs/{keg_id}/reviews",
                            json={"name": "Alice", "stars": 3}).json()["id"]
    r = client.delete(f"/api/reviews/{review_id}")
    assert r.status_code == 401


def test_delete_review_with_auth():
    token = get_token()
    keg_id = first_keg_id()
    review_id = client.post(f"/api/kegs/{keg_id}/reviews",
                            json={"name": "Alice", "stars": 3}).json()["id"]
    r = client.delete(f"/api/reviews/{review_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204
    assert client.get(f"/api/kegs/{keg_id}/reviews").json() == []


def test_delete_review_404():
    token = get_token()
    r = client.delete("/api/reviews/99999",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_review_on_unknown_keg():
    r = client.post("/api/kegs/99999/reviews", json={"name": "Alice", "stars": 3})
    assert r.status_code == 404
```

**Step 2: Run tests — expect ImportError / 404 failures**

```bash
cd api && python -m pytest tests/test_reviews_api.py -v 2>&1 | head -30
```
Expected: failures because the router doesn't exist yet.

**Step 3: Create `api/routers/reviews.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Keg, Review
from schemas import ReviewCreate, ReviewOut
from auth import get_current_user
from jose import JWTError

router = APIRouter(tags=["reviews"])
_bearer = HTTPBearer(auto_error=False)


def _require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return get_current_user(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/api/kegs/{keg_id}/reviews", response_model=List[ReviewOut])
def list_reviews(keg_id: int, db: Session = Depends(get_db)):
    if not db.query(Keg).filter(Keg.id == keg_id).first():
        raise HTTPException(status_code=404, detail="Keg not found")
    return (
        db.query(Review)
        .filter(Review.keg_id == keg_id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.post("/api/kegs/{keg_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(keg_id: int, body: ReviewCreate, db: Session = Depends(get_db)):
    if not db.query(Keg).filter(Keg.id == keg_id).first():
        raise HTTPException(status_code=404, detail="Keg not found")
    review = Review(keg_id=keg_id, name=body.name, stars=body.stars, comment=body.comment)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/api/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(_require_auth),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
```

**Step 4: Register router in `api/main.py`**

Add to the imports line:
```python
from routers import kegs, auth as auth_router, stats as stats_router, reviews as reviews_router
```

Add after the existing `app.include_router(stats_router.router)`:
```python
app.include_router(reviews_router.router)
```

**Step 5: Run tests — expect all green**

```bash
cd api && python -m pytest tests/test_reviews_api.py -v
```
Expected: all 13 tests PASS.

**Step 6: Commit**

```bash
git add api/routers/reviews.py api/tests/test_reviews_api.py api/main.py
git commit -m "feat: add reviews router (list, create, admin delete) with tests"
```

---

### Task 4: Attach avg_stars / review_count to keg list endpoint

**Files:**
- Modify: `api/routers/kegs.py`
- Modify: `api/tests/test_kegs_api.py`

**Step 1: Write the failing tests**

Append to `api/tests/test_kegs_api.py`:

```python
def test_keg_list_has_review_fields_when_empty():
    kegs = client.get("/api/kegs").json()
    assert kegs[0]["avg_stars"] is None
    assert kegs[0]["review_count"] == 0


def test_keg_list_avg_stars_computed():
    kegs_data = client.get("/api/kegs").json()
    keg_id = kegs_data[0]["id"]
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "A", "stars": 4})
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "B", "stars": 2})
    kegs_data = client.get("/api/kegs").json()
    k = next(k for k in kegs_data if k["id"] == keg_id)
    assert k["avg_stars"] == 3.0
    assert k["review_count"] == 2


def test_get_keg_by_id_has_review_fields():
    kegs_data = client.get("/api/kegs").json()
    keg_id = kegs_data[0]["id"]
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "A", "stars": 5})
    r = client.get(f"/api/kegs/{keg_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["avg_stars"] == 5.0
    assert data["review_count"] == 1
```

**Step 2: Run — expect failures**

```bash
cd api && python -m pytest tests/test_kegs_api.py::test_keg_list_has_review_fields_when_empty tests/test_kegs_api.py::test_keg_list_avg_stars_computed tests/test_kegs_api.py::test_get_keg_by_id_has_review_fields -v
```
Expected: KeyError or assertion failures.

**Step 3: Add `_attach_review_stats` helper and call it in `api/routers/kegs.py`**

Add to imports at the top of `api/routers/kegs.py`:
```python
from sqlalchemy import func
from models import Keg, Review
```
(Replace the existing `from models import Keg` line.)

Add the helper function after `_ensure_10_slots`:
```python
def _attach_review_stats(kegs: list, db: Session) -> list:
    if not kegs:
        return kegs
    ids = [k.id for k in kegs]
    stats = {
        keg_id: (avg, count)
        for keg_id, avg, count in db.query(
            Review.keg_id,
            func.avg(Review.stars),
            func.count(Review.id),
        )
        .filter(Review.keg_id.in_(ids))
        .group_by(Review.keg_id)
        .all()
    }
    for keg in kegs:
        avg, count = stats.get(keg.id, (None, 0))
        keg.avg_stars = round(float(avg), 1) if avg is not None else None
        keg.review_count = count
    return kegs
```

Update `list_kegs`:
```python
@router.get("", response_model=List[KegOut])
def list_kegs(db: Session = Depends(get_db)):
    _ensure_10_slots(db)
    kegs = db.query(Keg).order_by(Keg.slot).all()
    _attach_review_stats(kegs, db)
    return kegs
```

Update `get_keg`:
```python
@router.get("/{keg_id}", response_model=KegOut)
def get_keg(keg_id: int, db: Session = Depends(get_db)):
    _ensure_10_slots(db)
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    _attach_review_stats([keg], db)
    return keg
```

**Step 4: Run all tests**

```bash
cd api && python -m pytest -v
```
Expected: all tests PASS.

**Step 5: Commit**

```bash
git add api/routers/kegs.py api/tests/test_kegs_api.py
git commit -m "feat: attach avg_stars and review_count to keg endpoints"
```

---

### Task 5: Add review API functions to frontend

**Files:**
- Modify: `frontend/src/lib/api.js`

**Step 1: Append three exports to `api.js`**

At the end of `frontend/src/lib/api.js`, add:

```js
export const fetchReviews = (kegId) => request(`/kegs/${kegId}/reviews`);
export const submitReview = (kegId, data) =>
  request(`/kegs/${kegId}/reviews`, { method: 'POST', body: JSON.stringify(data) });
export const deleteReview = (reviewId) =>
  request(`/reviews/${reviewId}`, { method: 'DELETE' });
```

Note: `deleteReview` relies on `request()` which auto-attaches the JWT from `localStorage` — no token argument needed.

**Step 2: Verify build**

```bash
cd frontend && npm run check
```
Expected: no errors.

**Step 3: Commit**

```bash
git add frontend/src/lib/api.js
git commit -m "feat: add fetchReviews, submitReview, deleteReview to api.js"
```

---

### Task 6: Create StarRating.svelte component

**Files:**
- Create: `frontend/src/lib/StarRating.svelte`

**Step 1: Write the component**

```svelte
<script>
  import { createEventDispatcher } from 'svelte';

  export let value = 0;
  export let interactive = false;

  const dispatch = createEventDispatcher();
  let hovered = 0;

  function pick(n) {
    if (!interactive) return;
    dispatch('change', n);
  }
</script>

<span class="stars" class:interactive>
  {#each [1, 2, 3, 4, 5] as n}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <span
      class="star"
      class:filled={n <= (interactive ? (hovered || value) : value)}
      on:mouseenter={() => { if (interactive) hovered = n; }}
      on:mouseleave={() => { if (interactive) hovered = 0; }}
      on:click={() => pick(n)}
      role={interactive ? 'button' : undefined}
      tabindex={interactive ? 0 : undefined}
      on:keydown={(e) => e.key === 'Enter' && pick(n)}
      aria-label={interactive ? `Rate ${n} star${n > 1 ? 's' : ''}` : undefined}
    >★</span>
  {/each}
</span>

<style>
  .stars { display: inline-flex; gap: 2px; line-height: 1; }
  .star { color: #3a2f20; font-size: 1em; }
  .star.filled { color: #c8860a; }
  .interactive .star { cursor: pointer; transition: color 0.1s; }
  .interactive .star:focus { outline: 1px solid #c8860a; border-radius: 2px; }
</style>
```

**Step 2: Verify build**

```bash
cd frontend && npm run check
```
Expected: no errors.

**Step 3: Commit**

```bash
git add frontend/src/lib/StarRating.svelte
git commit -m "feat: add reusable StarRating.svelte component"
```

---

### Task 7: Add review panel to KegCard

**Files:**
- Modify: `frontend/src/lib/KegCard.svelte`

**Step 1: Add imports and review state to the `<script>` block**

In the `<script>` block of `frontend/src/lib/KegCard.svelte`, add to the imports:

```js
import StarRating from './StarRating.svelte';
import { fetchReviews, submitReview } from './api.js';
```

Add these state variables after the existing `let showRecipe = false;`:

```js
let showReviews = false;
let reviews = [];
let reviewsLoaded = false;
let reviewForm = { name: '', stars: 0, comment: '' };
let reviewSubmitting = false;
let reviewError = null;
let reviewSuccess = false;
let showAllReviews = false;

async function toggleReviews() {
  showReviews = !showReviews;
  if (showReviews && !reviewsLoaded) {
    reviews = await fetchReviews(keg.id);
    reviewsLoaded = true;
  }
}

async function handleSubmitReview() {
  if (!reviewForm.name.trim() || reviewForm.stars === 0) {
    reviewError = 'Name and a star rating are required.';
    return;
  }
  reviewSubmitting = true;
  reviewError = null;
  try {
    const created = await submitReview(keg.id, {
      name: reviewForm.name.trim(),
      stars: reviewForm.stars,
      comment: reviewForm.comment.trim() || null,
    });
    reviews = [created, ...reviews];
    reviewForm = { name: '', stars: 0, comment: '' };
    reviewSuccess = true;
    setTimeout(() => reviewSuccess = false, 3000);
  } catch (e) {
    reviewError = 'Could not submit review. Please try again.';
  } finally {
    reviewSubmitting = false;
  }
}

function relativeDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const diff = Math.floor((Date.now() - d) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  if (diff < 30) return `${diff}d ago`;
  return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
}

$: displayedReviews = showAllReviews ? reviews : reviews.slice(0, 5);
$: avgStars = keg.avg_stars;
$: reviewCount = keg.review_count ?? 0;
```

**Step 2: Add review section to the template**

Inside the `{:else}` block (non-empty keg), after the closing `{/if}` for `keg.notes`, add before the closing `</div>` of `.info`:

```svelte
<!-- Review strip -->
<div class="review-strip">
  <button type="button" class="review-toggle" on:click={toggleReviews}>
    <StarRating value={avgStars ?? 0} />
    {#if reviewCount > 0}
      <span class="review-meta">{avgStars} ★ ({reviewCount} {reviewCount === 1 ? 'review' : 'reviews'})</span>
    {:else}
      <span class="review-meta no-reviews">No reviews yet</span>
    {/if}
    <span class="chevron">{showReviews ? '▲' : '▼'}</span>
  </button>

  {#if showReviews}
    <div class="review-panel">
      {#each displayedReviews as rev (rev.id)}
        <div class="review-item">
          <div class="review-header">
            <strong>{rev.name}</strong>
            <StarRating value={rev.stars} />
            <span class="review-date">{relativeDate(rev.created_at)}</span>
          </div>
          {#if rev.comment}<p class="review-comment">"{rev.comment}"</p>{/if}
        </div>
      {/each}
      {#if reviews.length > 5 && !showAllReviews}
        <button type="button" class="show-all" on:click={() => showAllReviews = true}>
          Show all {reviews.length} reviews
        </button>
      {/if}

      <div class="review-form">
        <div class="form-row">
          <input
            class="form-input"
            placeholder="Your name"
            bind:value={reviewForm.name}
            maxlength="80"
          />
          <StarRating value={reviewForm.stars} interactive on:change={(e) => reviewForm.stars = e.detail} />
        </div>
        <textarea
          class="form-textarea"
          placeholder="Tasting notes (optional)"
          bind:value={reviewForm.comment}
          maxlength="500"
          rows="2"
        ></textarea>
        {#if reviewError}<p class="form-error">{reviewError}</p>{/if}
        {#if reviewSuccess}<p class="form-success">Review posted!</p>{/if}
        <button
          type="button"
          class="submit-btn"
          on:click={handleSubmitReview}
          disabled={reviewSubmitting}
        >
          {reviewSubmitting ? 'Posting…' : 'Post review'}
        </button>
      </div>
    </div>
  {/if}
</div>
```

**Step 3: Add styles**

Append to the `<style>` block of `KegCard.svelte`:

```css
  .review-strip { margin-top: 10px; border-top: 1px solid rgba(200,134,10,0.15); padding-top: 8px; }

  .review-toggle {
    display: flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: #9a8668; font-size: 12px; padding: 0; width: 100%; text-align: left;
  }
  .review-toggle:hover { color: #e8a020; }
  .review-meta { font-size: 11px; color: #7a6a54; }
  .review-meta.no-reviews { font-style: italic; }
  .chevron { margin-left: auto; font-size: 9px; color: #5a4a33; }

  .review-panel { margin-top: 8px; display: flex; flex-direction: column; gap: 8px; }

  .review-item { padding: 6px 0; border-bottom: 1px solid rgba(200,134,10,0.08); }
  .review-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .review-header strong { font-size: 12px; color: #c8b080; }
  .review-date { font-size: 10px; color: #5a4a33; margin-left: auto; }
  .review-comment { margin: 4px 0 0; font-size: 11px; color: #9a8668; font-style: italic; }

  .show-all {
    background: none; border: none; cursor: pointer;
    font-size: 11px; color: #7a6a54; text-decoration: underline; padding: 0;
  }

  .review-form { margin-top: 6px; display: flex; flex-direction: column; gap: 6px; }
  .form-row { display: flex; align-items: center; gap: 8px; }
  .form-input {
    flex: 1; background: rgba(255,255,255,0.04); border: 1px solid rgba(200,134,10,0.2);
    color: #f0e3c8; padding: 5px 8px; border-radius: 3px; font-size: 12px;
  }
  .form-input::placeholder { color: #5a4a33; }
  .form-textarea {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(200,134,10,0.2);
    color: #f0e3c8; padding: 5px 8px; border-radius: 3px; font-size: 12px;
    resize: vertical; font-family: inherit;
  }
  .form-textarea::placeholder { color: #5a4a33; }
  .form-error { font-size: 11px; color: #e06060; margin: 0; }
  .form-success { font-size: 11px; color: #6abf6a; margin: 0; }
  .submit-btn {
    align-self: flex-start;
    background: rgba(200,134,10,0.15); border: 1px solid rgba(200,134,10,0.35);
    color: #e8a020; padding: 5px 14px; border-radius: 3px; font-size: 12px;
    cursor: pointer; transition: background 0.15s;
  }
  .submit-btn:hover:not(:disabled) { background: rgba(200,134,10,0.28); }
  .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
```

**Step 4: Verify build**

```bash
cd frontend && npm run check && npm run build
```
Expected: no errors.

**Step 5: Commit**

```bash
git add frontend/src/lib/KegCard.svelte
git commit -m "feat: add collapsible review panel with star rating to KegCard"
```

---

### Task 8: Add review management to admin panel

**Files:**
- Modify: `frontend/src/routes/admin/+page.svelte`

**Step 1: Add deleteReview import**

In the `<script>` block of `admin/+page.svelte`, update the api.js import line to include:

```js
import { fetchKegs, updateKeg, clearKeg, uploadRecipe, deleteRecipe, recipeUrl, isLoggedIn, fetchReviews, deleteReview } from '$lib/api.js';
```

**Step 2: Add review state and handler to the `<script>` block**

Add after the existing state variables:

```js
let kegReviews = {};   // { [keg_id]: Review[] }

async function loadReviews(kegId) {
  kegReviews[kegId] = await fetchReviews(kegId);
  kegReviews = kegReviews;  // trigger reactivity
}

async function handleDeleteReview(kegId, reviewId) {
  await deleteReview(reviewId);
  kegReviews[kegId] = (kegReviews[kegId] ?? []).filter(r => r.id !== reviewId);
  kegReviews = kegReviews;
}
```

**Step 3: Add review section to each keg card in the admin template**

Find the admin keg card template (the element that shows each keg's info). After the existing keg details block, add a review section. Look for where `saving` / recipe buttons are rendered and add below:

```svelte
<!-- Reviews -->
<div class="admin-reviews">
  <button type="button" class="review-load-btn"
    on:click={() => kegReviews[keg.id] ? (kegReviews[keg.id] = undefined, kegReviews = kegReviews) : loadReviews(keg.id)}>
    {kegReviews[keg.id] ? 'Hide' : `Reviews (${keg.review_count ?? 0})`}
  </button>
  {#if kegReviews[keg.id]}
    {#if kegReviews[keg.id].length === 0}
      <p class="no-reviews-admin">No reviews.</p>
    {/if}
    {#each kegReviews[keg.id] as rev (rev.id)}
      <div class="admin-review-row">
        <span class="rev-name">{rev.name}</span>
        <span class="rev-stars">{'★'.repeat(rev.stars)}{'☆'.repeat(5 - rev.stars)}</span>
        {#if rev.comment}<span class="rev-comment">"{rev.comment}"</span>{/if}
        <button type="button" class="rev-delete"
          on:click={() => handleDeleteReview(keg.id, rev.id)}
          title="Delete review">✕</button>
      </div>
    {/each}
  {/if}
</div>
```

**Step 4: Add admin review styles**

In the `<style>` block of `admin/+page.svelte`, add:

```css
  .admin-reviews { margin-top: 10px; border-top: 1px solid rgba(200,134,10,0.15); padding-top: 8px; }
  .review-load-btn {
    background: none; border: 1px solid rgba(200,134,10,0.2);
    color: #9a8668; font-size: 11px; padding: 3px 10px; border-radius: 3px; cursor: pointer;
  }
  .review-load-btn:hover { border-color: rgba(200,134,10,0.5); color: #e8a020; }
  .no-reviews-admin { font-size: 11px; color: #5a4a33; font-style: italic; margin: 4px 0; }
  .admin-review-row {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    padding: 4px 0; border-bottom: 1px solid rgba(200,134,10,0.08); font-size: 12px;
  }
  .rev-name { color: #c8b080; font-weight: 600; }
  .rev-stars { color: #c8860a; letter-spacing: 1px; }
  .rev-comment { color: #9a8668; font-style: italic; flex: 1; }
  .rev-delete {
    margin-left: auto; background: none; border: none;
    color: #804040; cursor: pointer; font-size: 13px; padding: 0 4px;
  }
  .rev-delete:hover { color: #e06060; }
```

**Step 5: Verify build**

```bash
cd frontend && npm run check && npm run build
```
Expected: no errors.

**Step 6: Commit**

```bash
git add frontend/src/routes/admin/+page.svelte
git commit -m "feat: add review management (load + delete) to admin panel"
```

---

### Task 9: Full-stack smoke test

**Step 1: Start the backend**

```bash
cd api && uvicorn main:app --reload --port 8000
```

**Step 2: Verify reviews endpoints**

```bash
# Get keg list — should include avg_stars and review_count fields
curl -s http://localhost:8000/api/kegs | python3 -m json.tool | grep -E "avg_stars|review_count" | head -4

# Post a review (replace 1 with the actual keg id from the list)
curl -s -X POST http://localhost:8000/api/kegs/1/reviews \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","stars":4,"comment":"Tasty"}' | python3 -m json.tool

# Confirm it appears in the list
curl -s http://localhost:8000/api/kegs/1/reviews | python3 -m json.tool
```
Expected: review appears with `id`, `name`, `stars`, `comment`, `created_at`.

**Step 3: Run all backend tests**

```bash
cd api && python -m pytest -v
```
Expected: all tests PASS.

**Step 4: Build frontend**

```bash
cd frontend && npm run build
```
Expected: clean build, no errors.
