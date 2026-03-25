"""X-Ray monitoring module for NanoBot."""

try:
    import fastapi  # noqa: F401
    XRAY_AVAILABLE = True
except ImportError:
    XRAY_AVAILABLE = False
