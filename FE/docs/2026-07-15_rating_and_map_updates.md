(updated) See BE/docs or README for comments addition and rating behavior.

## Added Comments Feature
- Comments have `nickname`, `password`, `content`, and `post_id`.
- Endpoints added on BE:
  - POST `/api/comments/posts/{post_id}`
  - PUT `/api/comments/{comment_id}`
  - DELETE `/api/comments/{comment_id}`
- Posts now include `comments_count` which is updated when comments are created/deleted.

