from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from app.lib.trust_web.auth import generate_hash, verify
from app.lib.trust_web.store import ReleaseError, ReleaseStore


def test_password_and_bad_config():
    salt, encoded = generate_hash("local-test-password-only")
    assert verify("local-test-password-only", salt, encoded)
    assert not verify("different", salt, encoded)
    assert not verify("local-test-password-only", "bad", encoded)
    assert not verify("local-test-password-only", salt, "bad")


def test_private_release_fingerprint_and_paths(tmp_path: Path):
    release = tmp_path / "releases" / "20260918-1123"
    release.mkdir(parents=True)
    raw = gzip.compress(b'{"private":true}', mtime=0)
    payload = release / "roster.json.gz"
    payload.write_bytes(raw)
    blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    manifest = {"schema_version": 1, "release": "20260918-1123", "files": {
        "roster.json.gz": {"sha256": hashlib.sha256(raw).hexdigest(), "blob_sha": blob_sha}}}
    latest = tmp_path / "releases/current/manifest.json"
    latest.parent.mkdir()
    latest.write_text(json.dumps(manifest))
    store = ReleaseStore(local_root=tmp_path)
    assert store.read_json("roster.json.gz") == {"private": True}
    with pytest.raises(ReleaseError):
        store.read("../secret")
    with pytest.raises(ReleaseError):
        store.read("missing.json")
    bad = ReleaseStore(local_root=tmp_path)
    payload.write_bytes(b"tampered")
    with pytest.raises(ReleaseError, match="指纹"):
        bad.read("roster.json.gz")

    invalid = b"not-gzip"
    payload.write_bytes(invalid)
    manifest["files"]["roster.json.gz"]["sha256"] = hashlib.sha256(invalid).hexdigest()
    latest.write_text(json.dumps(manifest))
    with pytest.raises(ReleaseError, match="压缩"):
        ReleaseStore(local_root=tmp_path).read_json("roster.json.gz")


def test_no_unconfigured_private_store():
    with pytest.raises(ReleaseError):
        ReleaseStore()
