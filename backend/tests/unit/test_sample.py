"""
Sample test file to verify test infrastructure
"""
import pytest


def test_sample():
    """Basic test to verify pytest works"""
    assert True


def test_math():
    """Test basic math"""
    assert 1 + 1 == 2


@pytest.mark.parametrize(
    "input,expected",
    [
        (1, 2),
        (2, 4),
        (3, 6),
    ],
)
def test_double(input, expected):
    """Test parametrized tests work"""
    assert input * 2 == expected
