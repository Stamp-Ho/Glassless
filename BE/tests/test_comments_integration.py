import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure BE/src is on sys.path for tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.main import app


def test_create_comment_increments_post_comments_count():
    with TestClient(app) as client:
        # create a post
        post_payload = {
            "title": "test post",
            "content": "content",
            "password": "pw",
            "category": "잡담",
        }
        post_resp = client.post("/api/posts", json=post_payload)
        assert post_resp.status_code == 201
        post = post_resp.json()
        post_id = post["id"]
        assert post["comments_count"] == 0

        # create a comment
        comment_payload = {"nickname": "n", "password": "pw", "content": "hello"}
        comment_resp = client.post(f"/api/comments/posts/{post_id}", json=comment_payload)
        assert comment_resp.status_code == 201
        comment = comment_resp.json()
        assert comment["post_id"] == post_id

        # get post and verify comments_count
        get_post = client.get(f"/api/posts/{post_id}")
        assert get_post.status_code == 200
        get_post_json = get_post.json()
        assert get_post_json["comments_count"] == 1

        # list comments for post
        comments_list = client.get(f"/api/comments/posts/{post_id}")
        assert comments_list.status_code == 200
        comments = comments_list.json()
        assert any(c["id"] == comment["id"] for c in comments)
