import pytest

from app.shortener import DEFAULT_CODE_LENGTH, generate_short_code, is_valid_short_code


def test_generate_short_code_returns_default_length_code():
    url = "https://example.com"

    result = generate_short_code(url)

    assert isinstance(result, str)
    assert len(result) == DEFAULT_CODE_LENGTH


def test_generate_short_code_returns_custom_length_code():
    url = "https://example.com"

    result = generate_short_code(url, 8)

    assert isinstance(result, str)
    assert len(result) == 8


def test_generate_short_code_raises_error_for_empty_url():
    url = ""

    with pytest.raises(ValueError, match="URL cannot be empty"):
        generate_short_code(url)


def test_generate_short_code_raises_error_for_invalid_length():
    url = "https://example.com"

    with pytest.raises(ValueError, match="Length must be greater than 0"):
        generate_short_code(url, 0)


def test_is_valid_short_code_returns_true_for_valid_code():
    code = "abc123"

    result = is_valid_short_code(code)

    assert result is True


def test_is_valid_short_code_returns_false_for_wrong_length():
    code = "abc12"

    result = is_valid_short_code(code)

    assert result is False


def test_is_valid_short_code_returns_false_for_non_alphanumeric_code():
    code = "abc$12"

    result = is_valid_short_code(code)

    assert result is False
