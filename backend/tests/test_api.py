import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.schema import Notes, User
from backend.app.api.security import create_token, token_hash, verify_password


class APITests(unittest.TestCase):
    def setUp(self):
        self.settings = patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key-" * 4, "COOKIE_SECURE": "false"})
        self.settings.start()
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        def override_db():
            session = self.factory()
            try:
                yield session
            finally:
                session.close()
        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.settings.stop()

    def register(self, client=None, username="alice"):
        response = (client or self.client).post("/api/auth/register", json={
            "name": "Alice", "username": username, "password": "password123"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("password", response.json())
        self.assertNotIn("refreshtoken", response.json())
        return response.json()

    def login(self, client=None, username="alice", password="password123"):
        response = (client or self.client).post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def test_register_validation_and_duplicate(self):
        self.register(username="Alice")
        self.assertEqual(self.client.post("/api/auth/register", json={
            "name": "Other", "username": "alice", "password": "password123"}).status_code, 409)
        self.assertEqual(self.client.post("/api/auth/register", json={
            "name": " ", "username": "ab", "password": "short"}).status_code, 422)
        with self.factory() as db:
            user = db.query(User).one()
            self.assertNotEqual(user.password, "password123")
            self.assertTrue(verify_password("password123", user.password))

    def test_login_cookie_flags_and_invalid_password(self):
        self.register()
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "alice", "password": "wrong"}).status_code, 401)
        response = self.login()
        self.assertTrue(all("HttpOnly" in value and "SameSite=lax" in value for value in response.headers.get_list("set-cookie")))
        with self.factory() as db:
            self.assertEqual(db.query(User).one().refreshtoken, token_hash(self.client.cookies.get("refresh_token")))
        self.assertEqual(self.client.get("/api/users/me").json()["username"], "alice")

    def test_notes_crud_and_pagination(self):
        self.register()
        self.login()
        created = self.client.post("/api/notes", json={"content": "First"})
        self.assertEqual(created.status_code, 201)
        note_id = created.json()["id"]
        self.assertEqual(self.client.get("/api/notes/{}".format(note_id)).json()["content"], "First")
        for method in (self.client.patch, self.client.put):
            self.assertEqual(method("/api/notes/{}".format(note_id), json={"content": "Updated"}).json()["content"], "Updated")
        self.assertEqual(len(self.client.get("/api/notes?limit=1").json()), 1)
        self.assertEqual(self.client.get("/api/notes?offset=1").json(), [])
        self.assertEqual(self.client.post("/api/notes", json={"content": " "}).status_code, 422)
        self.assertEqual(self.client.delete("/api/notes/{}".format(note_id)).status_code, 204)
        self.assertEqual(self.client.get("/api/notes/{}".format(note_id)).status_code, 404)

    def test_other_user_cannot_access_notes(self):
        self.register()
        self.login()
        note_id = self.client.post("/api/notes", json={"content": "Private"}).json()["id"]
        with TestClient(app) as other:
            self.register(other, "bob")
            self.login(other, "bob")
            self.assertEqual(other.get("/api/notes").json(), [])
            self.assertEqual(other.get("/api/notes/{}".format(note_id)).status_code, 404)
            self.assertEqual(other.patch("/api/notes/{}".format(note_id), json={"content": "Intrusion"}).status_code, 404)
            self.assertEqual(other.delete("/api/notes/{}".format(note_id)).status_code, 404)

    def test_refresh_rotation_and_logout_revoke_old_tokens(self):
        self.register()
        self.login()
        old_access = self.client.cookies.get("access_token")
        old_refresh = self.client.cookies.get("refresh_token")
        self.assertEqual(self.client.post("/api/auth/refresh").status_code, 200)
        access = self.client.cookies.get("access_token")
        refresh = self.client.cookies.get("refresh_token")
        self.assertNotEqual(refresh, old_refresh)
        with TestClient(app) as replay:
            replay.cookies.set("access_token", old_access)
            replay.cookies.set("refresh_token", old_refresh)
            self.assertEqual(replay.get("/api/users/me").status_code, 401)
            self.assertEqual(replay.post("/api/auth/refresh").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertFalse(self.client.cookies)
        with self.factory() as db:
            self.assertIsNone(db.query(User).one().refreshtoken)
        self.client.cookies.set("access_token", access)
        self.client.cookies.set("refresh_token", refresh)
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/refresh").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)

    def test_password_update_revokes_session(self):
        self.register()
        self.login()
        response = self.client.patch("/api/users/me", json={"name": "New Name", "password": "newpassword123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "New Name")
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "alice", "password": "password123"}).status_code, 401)
        self.login(password="newpassword123")

    def test_profile_delete_removes_notes(self):
        self.register()
        self.login()
        self.client.post("/api/notes", json={"content": "Deleted with owner"})
        self.assertEqual(self.client.delete("/api/users/me").status_code, 204)
        with self.factory() as db:
            self.assertEqual(db.query(User).count(), 0)
            self.assertEqual(db.query(Notes).count(), 0)
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)

    def test_expired_wrong_type_and_missing_tokens(self):
        user = self.register()
        self.assertEqual(self.client.get("/api/notes").status_code, 401)
        self.login()
        sid = token_hash(self.client.cookies.get("refresh_token"))
        self.client.cookies.clear()
        self.client.cookies.set("access_token", create_token(user["id"], "access", -60, sid=sid))
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)
        self.client.cookies.set("access_token", create_token(user["id"], "refresh", 60))
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)
        self.client.cookies.clear()
        self.assertEqual(self.client.post("/api/auth/refresh").status_code, 401)

    def test_profile_validation_and_conflict(self):
        self.register(username="bob")
        self.register()
        self.login()
        self.assertEqual(self.client.patch("/api/users/me", json={"username": "BOB"}).status_code, 409)
        self.assertEqual(self.client.patch("/api/users/me", json={"name": None}).status_code, 422)
        self.assertEqual(self.client.patch("/api/users/me", json={}).status_code, 422)
        self.assertEqual(self.client.patch("/api/users/me", json={"username": "alice_new"}).json()["username"], "alice_new")

    def test_csrf_origin_rejected(self):
        self.assertEqual(self.client.post("/api/auth/logout", headers={"Origin": "https://untrusted.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout", headers={"Origin": "http://testserver"}).status_code, 204)


if __name__ == "__main__":
    unittest.main()
