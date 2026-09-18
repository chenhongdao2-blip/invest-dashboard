"""Print a new salt and hash for manual entry in Streamlit Secrets; never logs the password."""
from __future__ import annotations
import getpass
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))
from lib.trust_web.auth import generate_hash

password = getpass.getpass("Choose the Trust Research access password: ")
if len(password) < 16:
    raise SystemExit("Please use a password of at least 16 characters.")
salt, hashed = generate_hash(password)
print(f'TRUST_PASSWORD_SALT = "{salt}"')
print(f'TRUST_PASSWORD_HASH = "{hashed}"')
