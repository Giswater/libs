import os
import sys
import pytest
from unittest.mock import patch
from pathlib import Path

# Add the plugin directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs import tools_os

def test_get_datadir():
    """Test get_datadir function"""
    # Test Windows
    with patch('sys.platform', 'win32'):
        result = tools_os.get_datadir()
        assert isinstance(result, Path)
        # Normalize path separators for comparison
        assert str(result).replace('\\', '/').endswith("AppData/Roaming")
        # Test that it's a subdirectory of home
        assert str(result).startswith(str(Path.home()))

    # Test Linux
    with patch('sys.platform', 'linux'):
        result = tools_os.get_datadir()
        assert isinstance(result, Path)
        # Normalize path separators for comparison
        assert str(result).replace('\\', '/').endswith(".local/share")
        assert str(result).startswith(str(Path.home()))

    # Test macOS
    with patch('sys.platform', 'darwin'):
        result = tools_os.get_datadir()
        assert isinstance(result, Path)
        assert str(result).replace('\\', '/').endswith("Library/Application Support")
        assert str(result).startswith(str(Path.home()))

    # Test invalid platform
    with patch('sys.platform', 'invalid'):
        with pytest.raises(NotImplementedError):
            tools_os.get_datadir()

def test_set_boolean():
    """Test set_boolean function"""
    # Test True values
    assert tools_os.set_boolean(True) is True
    assert tools_os.set_boolean("TRUE") is True
    assert tools_os.set_boolean("True") is True
    assert tools_os.set_boolean("true") is True
    assert tools_os.set_boolean(1) is True
    assert tools_os.set_boolean("1") is True

    # Test False values
    assert tools_os.set_boolean(False) is False
    assert tools_os.set_boolean("FALSE") is False
    assert tools_os.set_boolean("False") is False
    assert tools_os.set_boolean("false") is False
    assert tools_os.set_boolean(0) is False
    assert tools_os.set_boolean("0") is False

    # Test default value
    assert tools_os.set_boolean("invalid", default=True) is True
    assert tools_os.set_boolean("invalid", default=False) is False

    # Test edge cases
    assert tools_os.set_boolean(None, default=True) is True
    assert tools_os.set_boolean("", default=False) is False
    assert tools_os.set_boolean(" ", default=True) is True
    assert tools_os.set_boolean("invalid", default=True) is True
    assert tools_os.set_boolean("invalid", default=False) is False

    # Test numeric strings
    assert tools_os.set_boolean("1", default=False) is True
    assert tools_os.set_boolean("0", default=True) is False
    assert tools_os.set_boolean("2", default=False) is False  # Not in bool_dict, should return default
    assert tools_os.set_boolean("-1", default=True) is True   # Not in bool_dict, should return default

def test_get_values_from_dictionary():
    """Test get_values_from_dictionary function"""
    # Test basic dictionary
    test_dict = {'a': 1, 'b': 2, 'c': 3}
    result = tools_os.get_values_from_dictionary(test_dict)
    assert list(result) == [1, 2, 3]

    # Test empty dictionary
    empty_dict = {}
    result = tools_os.get_values_from_dictionary(empty_dict)
    assert list(result) == []

    # Test dictionary with None values
    none_dict = {'a': None, 'b': None}
    result = tools_os.get_values_from_dictionary(none_dict)
    assert list(result) == [None, None]

    # Test dictionary with mixed types
    mixed_dict = {'a': 1, 'b': 'two', 'c': [3, 4]}
    result = tools_os.get_values_from_dictionary(mixed_dict)
    assert list(result) == [1, 'two', [3, 4]]

    # Test dictionary with duplicate values
    dup_dict = {'a': 1, 'b': 1, 'c': 2}
    result = tools_os.get_values_from_dictionary(dup_dict)
    assert list(result) == [1, 1, 2]

def test_open_file_path(mock_file_dialog):
    """Test open_file_path function"""
    path, filter_ = tools_os.open_file_path()
    assert path == "/test/path"
    assert filter_ == "All Files (*.*)"

def test_get_relative_path():
    """Test get_relative_path function"""
    # Test with different levels
    test_path = "/a/b/c/d/e/f.txt"

    # Level 0 (should return full path)
    result = tools_os.get_relative_path(test_path, 0)
    assert result.replace('\\', '/') == "f.txt"

    # Level 1
    result = tools_os.get_relative_path(test_path, 1)
    assert result.replace('\\', '/') == "e/f.txt"

    # Level 2
    result = tools_os.get_relative_path(test_path, 2)
    assert result.replace('\\', '/') == "d/e/f.txt"

    # Level 3
    result = tools_os.get_relative_path(test_path, 3)
    assert result.replace('\\', '/') == "c/d/e/f.txt"

    # Test with empty path
    result = tools_os.get_relative_path("", 1)
    assert result == ""

    # Test with relative path
    result = tools_os.get_relative_path("a/b/c.txt", 1)
    assert result.replace('\\', '/') == "b/c.txt"

    # Test with level greater than path depth
    result = tools_os.get_relative_path("a/b.txt", 5)
    assert result.replace('\\', '/') == "a/b.txt"

def test_ireplace():
    """Test ireplace function"""
    # Basic case-insensitive replacement
    text = "Hello World, hello world, HELLO WORLD"
    result = tools_os.ireplace("hello", "hi", text)
    assert result == "hi World, hi world, hi WORLD"

    # Test with empty strings
    assert tools_os.ireplace("", "hi", text) == text
    assert tools_os.ireplace("hello", "", text) == " World,  world,  WORLD"

    # Test with special characters
    text = "Hello*World, hello*world, HELLO*WORLD"
    result = tools_os.ireplace("hello*", "hi-", text)
    assert result == "hi-World, hi-world, hi-WORLD"

    # Test with overlapping patterns
    text = "HelloHelloHello"
    result = tools_os.ireplace("Hello", "Hi", text)
    assert result == "HiHiHi"

    # Test with no matches
    result = tools_os.ireplace("xyz", "hi", text)
    assert result == text

    # Test with regex special characters
    text = "Hello.World"
    result = tools_os.ireplace("hello.", "hi-", text)
    assert result == "hi-World"
