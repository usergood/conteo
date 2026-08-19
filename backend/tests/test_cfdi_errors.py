"""Tests for SAT/PAC error code mapping (ticket 10)."""

from app.cfdi.errors import ERROR_CODES, format_pac_error, get_error_info


class TestGetErrorInfo:
    def test_known_codes_return_full_info(self):
        for code in ERROR_CODES:
            info = get_error_info(code)
            assert "title" in info
            assert "description" in info
            assert "user_message" in info
            assert "remediation_steps" in info
            assert "severity" in info
            assert isinstance(info["remediation_steps"], list)
            assert len(info["remediation_steps"]) >= 1

    def test_unknown_code_returns_fallback(self):
        info = get_error_info("9999")
        assert "9999" in info["title"]
        assert "9999" in info["description"]
        assert "9999" in info["user_message"]
        assert info["severity"] == "error"

    def test_xml_structure_codes_are_errors(self):
        for code in ["201", "202", "203", "204", "205"]:
            assert ERROR_CODES[code]["severity"] == "error"

    def test_duplicate_and_exchange_warnings(self):
        assert ERROR_CODES["301"]["severity"] == "warning"
        assert ERROR_CODES["601"]["severity"] == "warning"
        assert ERROR_CODES["602"]["severity"] == "warning"

    def test_cancellation_is_error(self):
        assert ERROR_CODES["302"]["severity"] == "error"


class TestFormatPacError:
    def test_includes_all_fields(self):
        result = format_pac_error("201", "Missing namespace")
        assert result["code"] == "201"
        assert result["title"] == ERROR_CODES["201"]["title"]
        assert result["detail"] == "Missing namespace"
        assert result["severity"] == "error"

    def test_unknown_code_with_detail(self):
        result = format_pac_error("999", "Something broke")
        assert result["code"] == "999"
        assert result["detail"] == "Something broke"

    def test_empty_detail(self):
        result = format_pac_error("501")
        assert result["detail"] == ""

    def test_all_expected_keys_present(self):
        result = format_pac_error("202")
        expected_keys = {
            "code", "title", "description", "user_message",
            "remediation_steps", "severity", "detail",
        }
        assert set(result.keys()) == expected_keys
