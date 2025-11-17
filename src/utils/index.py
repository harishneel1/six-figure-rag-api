from urllib.parse import urlparse


def validate_url(url_string: str) -> bool:
    if not isinstance(url_string, str) or not url_string.strip():
        return False

    try:
        parsed_url = urlparse(url_string)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)
    except Exception:
        # Catch any parsing errors for malformed URLs
        return False
