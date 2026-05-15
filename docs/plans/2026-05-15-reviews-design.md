# Reviews & Star Ratings — Design

**Date:** 2026-05-15  
**Status:** Approved

## Summary

Add a per-keg review system to the public display: any visitor supplies a display name, picks 1–5 stars, and optionally writes a tasting note. Reviews are persisted. The admin can delete reviews from the admin panel.

---

## Data Layer

New `Review` SQLAlchemy model (`models.py`):

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK autoincrement |
| `keg_id` | INTEGER | FK → `kegs.id`, not null |
| `name` | TEXT | not null, trimmed, ≤ 80 chars |
| `stars` | INTEGER | 1–5, not null |
| `comment` | TEXT | nullable, ≤ 500 chars |
| `created_at` | DATETIME UTC | default now |

Table created by `Base.metadata.create_all()` on first boot (new table, not a column migration — no ALTER TABLE needed).

`KegOut` gains two computed read-only fields populated via subquery on every read:
- `avg_stars: float | None`
- `review_count: int`

New Pydantic schemas:
- `ReviewCreate` — `name`, `stars`, optional `comment`
- `ReviewOut` — `id`, `keg_id`, `name`, `stars`, `comment`, `created_at`

---

## API Endpoints

New `routers/reviews.py`:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/kegs/{keg_id}/reviews` | none | List reviews for a keg, newest first |
| POST | `/api/kegs/{keg_id}/reviews` | none | Submit a review |
| DELETE | `/api/reviews/{review_id}` | admin JWT | Delete a review (moderation) |

Validation on POST:
- `name`: trimmed, non-empty, max 80 chars
- `stars`: integer in [1, 5]
- `comment`: optional, max 500 chars

DELETE is at `/api/reviews/{review_id}` (not nested under kegs) so admin can target reviews without knowing `keg_id`.

---

## Frontend

### KegCard (`lib/KegCard.svelte`)

Non-empty kegs only. New section at the bottom of `.info`:

1. **Summary bar** — star icons + score + count (e.g. "4.2 ★ (7 reviews)" or "No reviews yet"). Clicking toggles the review panel.
2. **Review panel** (expanded):
   - List of existing reviews: name, stars, comment, relative date. Newest first, max 5 shown; "Show all" expands the rest.
   - "Write a review" form: name input → star picker → optional textarea → Submit.
   - On successful submit: form clears, review list refreshes in place.

### Admin Panel (`routes/admin/+page.svelte`)

Each review row in the review list gets a trash icon. Clicking calls `DELETE /api/reviews/{id}` with the stored JWT and removes the row optimistically.

### New component: `lib/StarRating.svelte`

Reusable star widget. Props:
- `value: number` — current value (0–5, supports half-stars for display)
- `interactive: boolean` — if true, hoverable/clickable picker; if false, read-only display
- `on:change` event dispatched on click

### `lib/api.js` additions

```js
fetchReviews(kegId)               // GET /api/kegs/{kegId}/reviews
submitReview(kegId, { name, stars, comment })  // POST
deleteReview(reviewId, token)     // DELETE /api/reviews/{reviewId}
```

---

## Out of Scope

- Per-session vote deduplication (localStorage guard)
- Pagination beyond "show all" toggle
- Email notifications
- Review editing
