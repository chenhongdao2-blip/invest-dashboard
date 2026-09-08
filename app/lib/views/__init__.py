"""Domain-parameterized page bodies.

R3 audit §7/§8.4: the Healthcare and AI navigation entries rendered the same
screen from two near-identical files (SEC Facts 92% shared, Valuation 76%,
Heatmap 88%), so every fix had to be applied twice. The body now lives here once
and takes `domain`; `app/pages/*.py` are thin shims that keep one `st.Page`
registration — and therefore one `url_path` deep-link — per nav entry.

Each module exposes `render(domain: str) -> None` and a `_DOMAINS` table holding
everything that genuinely differed between the two originals.
"""
