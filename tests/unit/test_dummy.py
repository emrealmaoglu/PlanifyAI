"""Dummy test to verify pytest setup"""
import pytest


def test_pytest_working():
    """Verify pytest is working"""
    assert True


def test_math():
    """Basic math test"""
    assert 1 + 1 == 2


@pytest.mark.skip(reason="Example of skipped test")
def test_skipped():
    """This test should be skipped"""
    assert False
