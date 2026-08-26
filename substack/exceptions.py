import json
import re


def _redact_message(text: str) -> str:
    if not text:
        return text
    # Redact common cookie-like values and session tokens
    # e.g., s%3A... or s:... which are typical for express session cookies
    text = re.sub(r"s%3A[a-zA-Z0-9_\-\.\%]+", "[REDACTED_COOKIE]", text)
    text = re.sub(r"s:[a-zA-Z0-9_\-\.\%]+", "[REDACTED_COOKIE]", text)
    return text


class SubstackAPIException(Exception):
    def __init__(self, status_code, text):
        text = _redact_message(text)
        try:
            json_res = json.loads(text)
        except ValueError:
            self.message = f"Invalid JSON error message from Substack: {text}"
        else:
            self.message = ", ".join(
                list(
                    map(lambda error: error.get("msg", ""), json_res.get("errors", []))
                )
            )
            self.message = self.message or json_res.get("error", "")
        self.status_code = status_code

    def __str__(self):
        return f"APIError(code={self.status_code}): {self.message}"


class SubstackRequestException(Exception):
    def __init__(self, message):
        self.message = _redact_message(message)

    def __str__(self):
        return f"SubstackRequestException: {self.message}"


class SectionNotExistsException(SubstackRequestException):
    pass
