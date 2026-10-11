"""Unit tests kontrol akses per role dan per kelas untuk mencegah BOLA."""
from types import SimpleNamespace

import pytest

from app.core.exceptions import AccessDeniedError
from app.services.access_control import (
    ensure_staff_role,
    ensure_student_data_access,
    get_accessible_class_scopes,
)


class _Assignments:
    def __init__(self, scopes):
        self.scopes = scopes
        self.called = False

    def list_scopes(self, user_id):
        self.called = True
        return list(self.scopes)


def test_non_staff_roles_are_denied_before_assignment_query():
    assignments = _Assignments([("X TKJ 1", "TKJ")])
    with pytest.raises(AccessDeniedError):
        get_accessible_class_scopes(SimpleNamespace(id=1, role="student"), assignments)
    assert assignments.called is False


@pytest.mark.parametrize("role", ["guru_bk", "wali_kelas"])
def test_staff_roles_are_normalized(role):
    ensure_staff_role(SimpleNamespace(role=role))


def test_user_without_assignments_is_default_denied():
    assignments = _Assignments([])
    with pytest.raises(AccessDeniedError, match="belum memiliki penugasan"):
        get_accessible_class_scopes(SimpleNamespace(id=3, role="wali_kelas"), assignments)


def test_same_role_cannot_access_unassigned_class_student():
    assignments = _Assignments([("X TKJ 1", "TKJ")])
    user = SimpleNamespace(id=7, role="wali_kelas")
    target = SimpleNamespace(class_name="XI RPL 2", major="RPL")
    with pytest.raises(AccessDeniedError, match="tidak berwenang mengakses siswa"):
        ensure_student_data_access(user, target, assignments)


def test_assigned_class_and_major_is_allowed():
    assignments = _Assignments([("X TKJ 1", "TKJ")])
    user = SimpleNamespace(id=7, role="wali_kelas")
    target = SimpleNamespace(class_name="X TKJ 1", major="TKJ")
    ensure_student_data_access(user, target, assignments)
