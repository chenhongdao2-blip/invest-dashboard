"""Read immutable private release objects after the page's password gate.

In local development TRUST_DATA_DIR points to the prepared release root. Cloud
uses a read-only GitHub token kept in Streamlit Secrets. No private data file is
part of the public invest-dashboard checkout or served static directory.
"""
from __future__ import annotations

import base64
import binascii
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_REPO = "chenhongdao2-blip/invest-dashboard-private-data"
_API = f"https://api.github.com/repos/{_REPO}"


class ReleaseError(RuntimeError):
    pass


class ReleaseStore:
    def __init__(self, *, local_root: str | Path | None = None, token: str = ""):
        self.local_root = Path(local_root).resolve() if local_root else None
        self.token = token.strip()
        if not self.local_root and not self.token:
            raise ReleaseError("私有研究数据读取凭据未配置。")
        self._manifest = None
        self._cache = {}

    def _api(self, url: str) -> dict:
        req = Request(url, headers={"Authorization": f"Bearer {self.token}",
                                    "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                                    "User-Agent": "invest-dashboard-trust-web"})
        try:
            with urlopen(req, timeout=25) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ReleaseError("私有研究数据暂时不可用或读取权限失效。") from exc

    def manifest(self) -> dict:
        if self._manifest is None:
            if self.local_root:
                path = self.local_root / "releases/current/manifest.json"
                try:
                    meta = json.loads(path.read_text())
                except (OSError, ValueError) as exc:
                    raise ReleaseError("私有研究清单未配置或已损坏。") from exc
            else:
                response = self._api(f"{_API}/contents/releases/current/manifest.json")
                if response.get("encoding") != "base64":
                    raise ReleaseError("私有研究清单响应格式错误。")
                try:
                    meta = json.loads(base64.b64decode(response["content"], validate=True))
                except (KeyError, ValueError, binascii.Error) as exc:
                    raise ReleaseError("私有研究清单响应已损坏。") from exc
            if (meta.get("schema_version") != 1 or not isinstance(meta.get("files"), dict)
                    or not re.fullmatch(r"[0-9]{8}-[0-9]{4}", str(meta.get("release", "")))):
                raise ReleaseError("私有研究版本不兼容。")
            self._manifest = meta
        return self._manifest

    def read(self, rel: str) -> bytes:
        meta = self.manifest()
        entry = meta["files"].get(rel)
        if not entry or rel.startswith("/") or ".." in Path(rel).parts:
            raise ReleaseError("研究资料未收录在本次发布版本。")
        if not re.fullmatch(r"[0-9a-f]{40}", str(entry.get("blob_sha", ""))):
            raise ReleaseError("研究资料清单指纹无效。")
        if rel not in self._cache:
            if self.local_root:
                path = (self.local_root / "releases" / meta["release"] / rel).resolve()
                root = (self.local_root / "releases" / meta["release"]).resolve()
                if not path.is_relative_to(root):
                    raise ReleaseError("研究资料路径无效。")
                try:
                    data = path.read_bytes()
                except OSError as exc:
                    raise ReleaseError("研究资料文件缺失。") from exc
            else:
                response = self._api(f"{_API}/git/blobs/{entry['blob_sha']}")
                if response.get("encoding") != "base64":
                    raise ReleaseError("研究资料响应格式错误。")
                try:
                    data = base64.b64decode(response["content"], validate=True)
                except (KeyError, ValueError, binascii.Error) as exc:
                    raise ReleaseError("研究资料响应已损坏。") from exc
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ReleaseError("研究资料指纹不符，拒绝展示。")
            self._cache[rel] = data
        return self._cache[rel]

    def read_json(self, rel: str) -> dict:
        try:
            return json.loads(gzip.decompress(self.read(rel)))
        except (OSError, ValueError) as exc:
            raise ReleaseError("研究资料压缩内容已损坏。") from exc

    def report(self, report_id: str) -> tuple[bytes, str]:
        if not report_id.isdecimal() or len(report_id) > 24:
            raise ReleaseError("研究报告编号无效。")
        try:
            return gzip.decompress(self.read(f"reports/{report_id}.md.gz")), "text/plain"
        except OSError as exc:
            raise ReleaseError("研究报告压缩内容已损坏。") from exc

    def evidence(self, name: str) -> tuple[bytes, str]:
        # The published reference uses evidence/<content-hash>.pdf/html.
        file_name = Path(name.split("#", 1)[0]).name
        if not file_name or not file_name.endswith((".pdf", ".html")):
            raise ReleaseError("研究来源格式不受支持。")
        rel = "evidence/" + file_name + ".gz"
        try:
            raw = gzip.decompress(self.read(rel))
        except OSError as exc:
            raise ReleaseError("研究来源压缩内容已损坏。") from exc
        expected = self.manifest()["files"][rel].get("original_sha256")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ReleaseError("研究来源原文指纹不符。")
        return raw, "application/pdf" if file_name.endswith(".pdf") else "text/html"


def store_from_settings(st) -> ReleaseStore:
    local = os.environ.get("TRUST_DATA_DIR")
    if local:
        return ReleaseStore(local_root=local)
    try:
        token = st.secrets.get("TRUST_DATA_GITHUB_TOKEN", "")
    except FileNotFoundError:
        token = ""
    return ReleaseStore(token=token)
