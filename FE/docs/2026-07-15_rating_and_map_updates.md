<<<<<<< HEAD
(updated) See BE/docs or README for comments addition and rating behavior.

## Added Comments Feature
- Comments have `nickname`, `password`, and `content`. `post_id` is provided as the URL path parameter for the POST endpoint.
- Endpoints added on BE:
  - POST `/api/comments/posts/{post_id}`
  - PUT `/api/comments/{comment_id}`
  - DELETE `/api/comments/{comment_id}`
- Posts now include `comments_count` which is updated when comments are created/deleted.

=======
# 2026-07-15 — Rating & Map UX + Backend Support

This document summarizes the changes made on 2026-07-15 to support ratings, map UI updates, and post flow. Apply / review these changes and run the notes below.

## Summary of changes

### Frontend (FE)
- File: `FE/src/views/PostListView.vue`
  - Added rating UI (5 star) in the post creation form.
  - Rating UI only shows when `category === '후기'` and a location is selected.
  - Rating click sets local `rating` state (no immediate server send).
  - When creating a `후기` post with a selected location and a rating, the frontend now:
    - Calls `POST /api/locations/{location_id}/ratings` and requires it to succeed.
    - If rating submission fails (429 or other), post creation is aborted and a failure modal is shown.
    - If rating submission succeeds, includes `rating` in the `POST /api/posts` payload.
  - Added toast + failure modal for rating errors.
  - Ensures client_id generation (IP + User-Agent hash) stored in `localStorage`.

- File: `FE/src/views/MapView.vue`
  - Loads Kakao key from `VITE_KAKAO_APP_KEY` in `.env`.
  - Map markers show rating info in InfoWindow; clicking marker fetches `/api/locations/{id}` to show latest `rating_avg` / `rating_count`.
  - Sidebar list and map list items display `rating_avg` and `rating_count` where available.
  - Display rules: ratings shown per-location independent of filters; Post-level rating UI is controlled by post category rules.

- File: `FE/src/views/DetailView.vue`
  - Shows `post.rating` for posts whose `category === '후기'` in the post header and in the linked location card.

- Env
  - File: `FE/.env` added with `VITE_KAKAO_APP_KEY` (local dev key).

### Backend (BE)
- File: `BE/src/app/models/post.py`
  - Added `rating_score` nullable integer column, and a `rating` property exposing it.

- File: `BE/src/app/schemas/post.py`
  - `PostCreate` now includes optional `rating: int | None` (1..5).
  - `PostResponse` and `PostListItem` include optional `rating: int | None`.

- File: `BE/src/app/routers/posts.py`
  - `create_post` writes `rating_score` (from payload.rating) when provided.
  - `list_posts` returns `rating` in list items.

## DB Migration
- The DB schema must be updated to add `rating_score` to the `posts` table (nullable integer).
- Example SQL (Postgres):

```sql
ALTER TABLE posts ADD COLUMN rating_score integer;
```

Or use your Alembic migration workflow to add a migration that creates the column.

## How the flow works now
- When user writes a post with category '후기' and selects a location and a star rating:
  1. Frontend calls POST `/api/locations/{location_id}/ratings` (payload: `{score, client_id}`).
  2. If rating POST succeeds, frontend includes `rating` in `POST /api/posts` body and creates the post.
  3. If rating POST fails (e.g. 429), frontend shows a modal and aborts post creation.
- For viewing posts and lists, `rating` is returned from `GET /api/posts` and `GET /api/posts/{id}` and displayed when `post.category === '후기'`.

## Notes & TODOs
- Ensure DB migration is applied before creating posts with ratings.
- Consider server behavior: ratings are also stored at location-level; ensure no semantic conflict between location ratings and post.rating.
- The frontend still stores a local submitted-record (localStorage) only after successful rating response; submissions are not blocked client-side.

---

If you want, I can:
- Create an Alembic migration file for `rating_score`.
- Commit & push this docs file and the FE changes (I can push FE branch as well).
- Run a quick integration test (curl) to POST a `후기` with `rating` once DB is migrated.
>>>>>>> frontend
