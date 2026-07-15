Summary: Clarified comments API payload and added tests

- Removed `post_id` from `CommentCreate` schema; `post_id` is passed via URL path for `POST /api/comments/posts/{post_id}`.
- Updated BE and FE docs to reflect that `post_id` is a path parameter.
- Added integration test `test_comments_integration.py` verifying comment creation increments `comments_count`.
- Added regression test `test_comments_regression.py` covering comment update/delete flows and password validation.
- Ran full BE test suite; all tests passed locally.

Files changed:
- BE/src/app/schemas/comment.py
- BE/README.md
- FE/docs/2026-07-15_rating_and_map_updates.md
- BE/tests/test_comments_integration.py
- BE/tests/test_comments_regression.py
- BE/docs/commit history/2026-07-15_comments_tests.md
