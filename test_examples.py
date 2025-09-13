#!/usr/bin/env python3
"""
Basic test examples for MoodleMagnet functions.
This demonstrates how tests could be structured for the project.

To run these tests:
    python test_examples.py

For a full test suite, consider using pytest:
    pip install pytest
    pytest test_examples.py -v
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moodlemagnet import clean_filename, validate_inputs, build_moodle_url


class TestMoodleMagnetFunctions(unittest.TestCase):
    """Test cases for MoodleMagnet helper functions."""
    
    def test_clean_filename_basic(self):
        """Test basic filename cleaning functionality."""
        url = "https://example.com/file.pdf?token=123&param=value"
        result = clean_filename(url)
        self.assertEqual(result, "file.pdf")
    
    def test_clean_filename_special_chars(self):
        """Test filename cleaning with Windows reserved characters."""
        url = "https://example.com/file<name>.pdf?token=123"
        result = clean_filename(url)
        self.assertEqual(result, "filename.pdf")
    
    def test_clean_filename_no_extension(self):
        """Test filename cleaning with no file extension."""
        url = "https://example.com/document?token=123"
        result = clean_filename(url)
        self.assertEqual(result, "document")
    
    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        result = validate_inputs("https://example.com", "valid_token")
        self.assertIsNone(result)
    
    def test_validate_inputs_empty_url(self):
        """Test input validation with empty URL."""
        result = validate_inputs("", "valid_token")
        self.assertIn("URL endpoint", result)
    
    def test_validate_inputs_empty_token(self):
        """Test input validation with empty token."""
        result = validate_inputs("https://example.com", "")
        self.assertIn("MOODLE_TOKEN", result)
    
    def test_validate_inputs_invalid_url(self):
        """Test input validation with invalid URL."""
        result = validate_inputs("not-a-url", "valid_token")
        self.assertIn("Not a valid URL", result)
    
    def test_build_moodle_url_basic(self):
        """Test basic Moodle URL building."""
        result = build_moodle_url("https://example.com", "test_function")
        expected = "https://example.com/moodle/webservice/rest/server.php?wsfunction=test_function&moodlewsrestformat=json"
        self.assertEqual(result, expected)
    
    def test_build_moodle_url_with_params(self):
        """Test Moodle URL building with parameters."""
        result = build_moodle_url("https://example.com", "test_function", courseid="123")
        expected = "https://example.com/moodle/webservice/rest/server.php?wsfunction=test_function&moodlewsrestformat=json&courseid=123"
        self.assertEqual(result, expected)
    
    def test_build_moodle_url_with_none_params(self):
        """Test Moodle URL building ignores None parameters."""
        result = build_moodle_url("https://example.com", "test_function", courseid="123", optional_param=None)
        expected = "https://example.com/moodle/webservice/rest/server.php?wsfunction=test_function&moodlewsrestformat=json&courseid=123"
        self.assertEqual(result, expected)


class TestDataStructuresFunctionality(unittest.TestCase):
    """Test cases for data structure deserialization."""
    
    def test_imports(self):
        """Test that datastructures module imports correctly."""
        try:
            import datastructures as ds
            # Test that main classes exist
            self.assertTrue(hasattr(ds, 'Section'))
            self.assertTrue(hasattr(ds, 'Module'))
            self.assertTrue(hasattr(ds, 'Content'))
            self.assertTrue(hasattr(ds, 'RecentCourse'))
        except ImportError as e:
            self.fail(f"Failed to import datastructures: {e}")


def run_basic_tests():
    """Run basic functionality tests without external dependencies."""
    print("Running basic MoodleMagnet functionality tests...")
    print("=" * 50)
    
    # Test 1: clean_filename function
    test_url = "https://example.com/document.pdf?token=12345&param=value"
    cleaned = clean_filename(test_url)
    print(f"✓ clean_filename test: '{test_url}' → '{cleaned}'")
    assert cleaned == "document.pdf", f"Expected 'document.pdf', got '{cleaned}'"
    
    # Test 2: validate_inputs function
    error = validate_inputs("", "token")
    print(f"✓ validate_inputs empty URL test: {error}")
    assert error is not None, "Should return error for empty URL"
    
    error = validate_inputs("https://example.com", "token")
    print(f"✓ validate_inputs valid inputs test: {error}")
    assert error is None, "Should return None for valid inputs"
    
    # Test 3: build_moodle_url function
    url = build_moodle_url("https://moodle.example.com", "test_function", courseid="123")
    expected_part = "moodle/webservice/rest/server.php"
    print(f"✓ build_moodle_url test: {url}")
    assert expected_part in url, f"URL should contain '{expected_part}'"
    assert "wsfunction=test_function" in url, "URL should contain function parameter"
    assert "courseid=123" in url, "URL should contain courseid parameter"
    
    print("=" * 50)
    print("✅ All basic tests passed!")
    

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        # Run basic tests without unittest framework
        run_basic_tests()
    else:
        # Run full unittest suite
        print("Running comprehensive test suite...")
        unittest.main(verbosity=2)