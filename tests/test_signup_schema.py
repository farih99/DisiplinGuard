"""Signup publik tidak menerima role dari request."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate


def test_user_create_has_no_public_role_field():
    payload = UserCreate.model_validate({"email": "new@example.com", "password": "Password-Aman-123"})
    assert not hasattr(payload, "role")


def test_user_create_rejects_supplied_role():
    with pytest.raises(ValidationError):
        UserCreate.model_validate({
            "email": "attacker@example.com",
            "password": "Password-Aman-123",
            "role": "guru_bk",
        })
