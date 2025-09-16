#!/usr/bin/env python3
"""
Simple test script for HTTP utilities that doesn't require external internet access.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from http_utils import create_robust_session, RobustHTTPClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_client_creation():
    """Test that the HTTP client can be created properly."""
    print("Testing HTTP client creation...")
    
    try:
        client = create_robust_session()
        if client and isinstance(client, RobustHTTPClient):
            print("✅ HTTP client creation test passed")
            client.close()
            return True
        else:
            print("❌ HTTP client creation test failed")
            return False
    except Exception as e:
        print(f"❌ HTTP client creation test failed with exception: {e}")
        return False

def test_user_agent_generation():
    """Test that user agents are being generated."""
    print("Testing user agent generation...")
    
    try:
        client = create_robust_session()
        user_agents = client._get_user_agents()
        
        if user_agents and len(user_agents) > 0:
            print(f"✅ User agent generation test passed - {len(user_agents)} user agents available")
            client.close()
            return True
        else:
            print("❌ User agent generation test failed")
            client.close()
            return False
    except Exception as e:
        print(f"❌ User agent generation test failed with exception: {e}")
        return False

def test_headers_generation():
    """Test that headers are being generated properly."""
    print("Testing headers generation...")
    
    try:
        client = create_robust_session()
        headers = client._get_random_headers()
        
        required_headers = ["User-Agent", "Accept", "Accept-Language"]
        if all(header in headers for header in required_headers):
            print("✅ Headers generation test passed")
            client.close()
            return True
        else:
            print("❌ Headers generation test failed - missing required headers")
            client.close()
            return False
    except Exception as e:
        print(f"❌ Headers generation test failed with exception: {e}")
        return False

def test_session_configuration():
    """Test that the session is configured properly."""
    print("Testing session configuration...")
    
    try:
        client = create_robust_session(max_retries=5, backoff_factor=2.0, timeout=60)
        
        if (client.max_retries == 5 and 
            client.backoff_factor == 2.0 and 
            client.timeout == 60):
            print("✅ Session configuration test passed")
            client.close()
            return True
        else:
            print("❌ Session configuration test failed")
            client.close()
            return False
    except Exception as e:
        print(f"❌ Session configuration test failed with exception: {e}")
        return False

def test_context_manager():
    """Test that the context manager works properly."""
    print("Testing context manager...")
    
    try:
        with create_robust_session() as client:
            if client and isinstance(client, RobustHTTPClient):
                print("✅ Context manager test passed")
                return True
            else:
                print("❌ Context manager test failed")
                return False
    except Exception as e:
        print(f"❌ Context manager test failed with exception: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting HTTP utilities tests (offline mode)...\n")
    
    tests = [
        test_client_creation,
        test_user_agent_generation,
        test_headers_generation,
        test_session_configuration,
        test_context_manager
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
        print("🎉 All tests passed! HTTP utilities are properly configured.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())