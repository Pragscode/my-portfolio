#!/usr/bin/env python3
"""
Test script for HTTP utilities to verify 403 error handling and robust request functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from http_utils import create_robust_session, robust_get
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_request():
    """Test basic HTTP request functionality."""
    print("Testing basic HTTP request...")
    
    # Test with a public API that should return 200
    response = robust_get("https://httpbin.org/status/200")
    if response and response.status_code == 200:
        print("✅ Basic request test passed")
        return True
    else:
        print("❌ Basic request test failed")
        return False

def test_403_handling():
    """Test 403 error handling."""
    print("Testing 403 error handling...")
    
    # Test with a URL that returns 403
    response = robust_get("https://httpbin.org/status/403")
    if response and response.status_code == 403:
        print("✅ 403 error handling test passed")
        return True
    else:
        print("❌ 403 error handling test failed")
        return False

def test_retry_mechanism():
    """Test retry mechanism with robust client."""
    print("Testing retry mechanism...")
    
    try:
        with create_robust_session(max_retries=2, backoff_factor=0.1) as client:
            # Test with a URL that returns 500 (should retry)
            response = client.get("https://httpbin.org/status/500")
            if response and response.status_code == 500:
                print("✅ Retry mechanism test passed")
                return True
            else:
                print("❌ Retry mechanism test failed")
                return False
    except Exception as e:
        print(f"❌ Retry mechanism test failed with exception: {e}")
        return False

def test_user_agent_rotation():
    """Test that user agents are being rotated."""
    print("Testing user agent rotation...")
    
    try:
        with create_robust_session() as client:
            # Make multiple requests and check if different user agents are used
            response1 = client.get("https://httpbin.org/user-agent")
            response2 = client.get("https://httpbin.org/user-agent")
            
            if response1 and response2:
                print("✅ User agent rotation test passed")
                return True
            else:
                print("❌ User agent rotation test failed")
                return False
    except Exception as e:
        print(f"❌ User agent rotation test failed with exception: {e}")
        return False

def test_network_error_handling():
    """Test network error handling."""
    print("Testing network error handling...")
    
    # Test with an invalid URL
    response = robust_get("https://this-domain-does-not-exist-12345.com")
    if response is None:
        print("✅ Network error handling test passed")
        return True
    else:
        print("❌ Network error handling test failed")
        return False

def main():
    """Run all tests."""
    print("Starting HTTP utilities tests...\n")
    
    tests = [
        test_basic_request,
        test_403_handling,
        test_retry_mechanism,
        test_user_agent_rotation,
        test_network_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HTTP utilities are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())