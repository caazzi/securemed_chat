"""
Security regression tests for the 5 critical fixes.

Run with:
    python -m pytest tests/test_security.py -v
"""
import os
import re
import importlib


# ---------------------------------------------------------------------------
# P1: Hardcoded IP must not appear as the CHROMA_HOST default
# ---------------------------------------------------------------------------
class TestP1_NoHardcodedIP:
    def test_config_source_has_no_hardcoded_ip(self):
        """The config module source must not contain the old public IP."""
        import securemed_chat.core.config as cfg
        src_path = cfg.__file__
        with open(src_path) as f:
            source = f.read()
        assert "34.151.247.35" not in source, "Hardcoded IP still present in config.py"




# ---------------------------------------------------------------------------
# P2: API key must be enforced (ValueError when unset)
# ---------------------------------------------------------------------------
class TestP2_APIKeyEnforced:
    def test_config_raises_without_api_key(self):
        """Importing config with no SECUREMED_API_KEY must raise ValueError."""
        # Temporarily remove the key from the environment
        saved = os.environ.pop("SECUREMED_API_KEY", None)
        try:
            # Force reimport so the module-level check runs again
            import securemed_chat.core.config as cfg
            try:
                importlib.reload(cfg)
                assert False, "Expected ValueError was not raised"
            except ValueError as exc:
                assert "SECUREMED_API_KEY" in str(exc)
        finally:
            if saved is not None:
                os.environ["SECUREMED_API_KEY"] = saved


# ---------------------------------------------------------------------------
# P4: Gradio frontend must not have a default API key
# ---------------------------------------------------------------------------
class TestP4_NoDefaultKeyInGradio:
    def test_gradio_source_has_no_default_key(self):
        """The gradio_app.py must never contain a hardcoded default API key."""
        gradio_path = os.path.join(
            os.path.dirname(__file__), "..", "gradio", "gradio_app.py"
        )
        with open(gradio_path) as f:
            source = f.read()
        assert "your_default_secret_key_for_dev" not in source, (
            "Insecure default API key still present in gradio/gradio_app.py"
        )


# ---------------------------------------------------------------------------
# P5: Endpoints must not leak exception text to clients
# ---------------------------------------------------------------------------
class TestP5_ErrorResponsesSanitized:
    def test_endpoints_no_fstring_in_detail(self):
        """HTTPException detail args must not contain f-string {e} patterns."""
        endpoints_path = os.path.join(
            os.path.dirname(__file__),
            "..", "src", "securemed_chat", "api", "endpoints.py",
        )
        with open(endpoints_path) as f:
            source = f.read()
        # Match patterns like detail=f"...{e}" but NOT detail=str(e) (which is fine)
        leaky = re.findall(r'detail=f["\'].*\{e\}', source)
        assert leaky == [], (
            f"Found error details leaking exception text: {leaky}"
        )
