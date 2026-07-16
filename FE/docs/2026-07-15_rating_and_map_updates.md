(updated) See BE/docs or README for comments addition and rating behavior.

## Added Comments Feature
- Comments have `nickname`, `password`, and `content`. `post_id` is provided as the URL path parameter for the POST endpoint.
- Endpoints added on BE:
  - POST `/api/comments/posts/{post_id}`
  - PUT `/api/comments/{comment_id}`
  - DELETE `/api/comments/{comment_id}`
- Posts now include `comments_count` which is updated when comments are created/deleted.

