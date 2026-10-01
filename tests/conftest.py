import os

# app.auth.security reads the JWT secret at import time and refuses to
# start without one, so tests get a throwaway value if .env has none.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-0123")
