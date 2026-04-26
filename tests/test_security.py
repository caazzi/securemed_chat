"""
Security regression tests.

Run with:
    python -m pytest tests/test_security.py -v
"""
import os
import re
import importlib


# ---------------------------------------------------------------------------
# P1: Hardcoded IP must not appear in config
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
        saved = os.environ.pop("SECUREMED_API_KEY", None)
        try:
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
# P4: Reflex frontend must not have a hardcoded default API key
# ---------------------------------------------------------------------------
class TestP4_NoDefaultKeyInReflexFrontend:
    def test_reflex_state_has_no_default_key(self):
        """reflex_app/securemed/state.py must not contain a hardcoded default API key."""
        state_path = os.path.join(
            os.path.dirname(__file__), "..", "reflex_app", "securemed", "state.py"
        )
        with open(state_path) as f:
            source = f.read()
        assert "dev_key_123" not in source, (
            "Insecure default API key still present in reflex_app/securemed/state.py"
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

# ---------------------------------------------------------------------------
# P6: Auto destruction notices & Emergency rules
# ---------------------------------------------------------------------------
class TestP6_Sprint5Features:
    def test_auto_destruction_notice_en(self):
        from reflex_app.securemed.i18n import translations
        assert "deleted" in translations["en"]["complete_desc"].lower()

    def test_auto_destruction_notice_pt(self):
        from reflex_app.securemed.i18n import translations
        assert "apagados" in translations["pt"]["complete_desc"].lower()

    def test_emergency_rule_in_interview_prompt(self):
        from securemed_chat.services.agent_service import get_interview_chain
        chain = get_interview_chain()
        prompt = chain.steps[0]
        system_msg = str(prompt.messages[0])
        assert "emergency" in system_msg.lower()
        assert "do not generate questions" in system_msg.lower()
