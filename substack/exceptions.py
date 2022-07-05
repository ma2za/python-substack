import json


class SubstackAPIException(Exception):
    def __init__(self, status_code, text):
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
        self.message = message

    def __str__(self):
        return f"SubstackRequestException: {self.message}"
