import json


class SubstackAPIException(Exception):
    def __init__(self, status_code: int, text: str) -> None:
        try:
            json_res = json.loads(text)
        except ValueError:
            self.message = f"Invalid JSON error message from Substack: {text}"
        else:
            self.message = ", ".join(
                [error.get("msg", "") for error in json_res.get("errors", [])]
            )
            self.message = self.message or json_res.get("error", "")
        self.status_code = status_code

    def __str__(self) -> str:
        return f"APIError(code={self.status_code}): {self.message}"


class SubstackRequestException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return f"SubstackRequestException: {self.message}"


class SectionNotExistsException(SubstackRequestException):
    pass
