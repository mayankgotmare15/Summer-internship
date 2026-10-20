"""Unit tests for UUID and public ticket ID generation."""

import uuid
from src.core.ids import generate_uuid, generate_public_id


def test_generate_uuid():
    u1 = generate_uuid()
    u2 = generate_uuid()
    assert isinstance(u1, uuid.UUID)
    assert isinstance(u2, uuid.UUID)
    assert u1 != u2


def test_generate_public_id():
    id1 = generate_public_id("T")
    id2 = generate_public_id("T")
    assert id1.startswith("T-")
    assert id2.startswith("T-")
    num1 = int(id1.split("-")[1])
    num2 = int(id2.split("-")[1])
    assert num2 == num1 + 1
