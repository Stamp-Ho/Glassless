import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure BE/src is on sys.path for tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.main import app


def create_post(client):
    payload = {
        "title": "reg post",
        "content": "content",
        "password": "pw",
        "category": "잡담",
    }
    r = client.post("/api/posts", json=payload)
    assert r.status_code == 201
    return r.json()


def create_comment(client, post_id, password="pw"):
    payload = {"nickname": "n", "password": password, "content": "hello"}
    r = client.post(f"/api/comments/posts/{post_id}", json=payload)
    assert r.status_code == 201
    return r.json()


def test_comment_update_and_delete_flow():
    with TestClient(app) as client:
        post = create_post(client)
        post_id = post["id"]

        comment = create_comment(client, post_id, password="c_pw")
        comment_id = comment["id"]

        # wrong password for update
        bad_update = {"password": "wrong", "content": "new"}
        r = client.put(f"/api/comments/{comment_id}", json=bad_update)
        assert r.status_code == 403

        # correct update
        good_update = {"password": "c_pw", "content": "updated content"}
        r = client.put(f"/api/comments/{comment_id}", json=good_update)
        assert r.status_code == 200
        updated = r.json()
        assert updated["content"] == "updated content"

        # wrong password for delete
        bad_delete = {"password": "wrong", "content": "irrelevant"}
        r = client.request("DELETE", f"/api/comments/{comment_id}", json=bad_delete)
        assert r.status_code == 403

        # correct delete
        good_delete = {"password": "c_pw", "content": "irrelevant"}
        r = client.request("DELETE", f"/api/comments/{comment_id}", json=good_delete)
        assert r.status_code == 204

        # verify post comments_count decremented
        get_post = client.get(f"/api/posts/{post_id}")
        assert get_post.status_code == 200
        assert get_post.json()["comments_count"] == 0
