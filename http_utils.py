"""
HTTP Utility Module for Robust Request Handling

This module provides enhanced HTTP request functionality with:
- Comprehensive error handling for 403 Forbidden responses
- Retry mechanisms with exponential backoff
- User-agent rotation to avoid bot detection
- Session management for connection pooling
- Detailed logging for debugging HTTP issues
"""

import requests
import time
import random
import logging
from typing import Optional, Dict, Any, List
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustHTTPClient:
    """Enhanced HTTP client with robust error handling and anti-bot measures."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 backoff_factor: float = 1.0,
                 status_forcelist: List[int] = None,
                 timeout: int = 30):
        """
        Initialize the robust HTTP client.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Factor for exponential backoff between retries
            status_forcelist: HTTP status codes to retry on
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        
        if status_forcelist is None:
            # Include 403 in retry list as servers sometimes return it temporarily
            self.status_forcelist = [403, 429, 500, 502, 503, 504]
        else:
            self.status_forcelist = status_forcelist
            
        self.session = self._create_session()
        self.user_agents = self._get_user_agents()
        
    def _get_user_agents(self) -> List[str]:
        """Get a list of realistic user agents for rotation."""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
        ]
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=self.status_forcelist,
            backoff_factor=self.backoff_factor,
            raise_on_status=False  # Don't raise exception on retry-able status codes
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Generate randomized headers to avoid bot detection."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def _handle_403_error(self, response: requests.Response, url: str, attempt: int) -> None:
        """Handle 403 Forbidden errors with detailed logging."""
        logger.warning(f"403 Forbidden error for {url} (attempt {attempt + 1})")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        # Log potential causes
        if 'cloudflare' in response.headers.get('server', '').lower():
            logger.info("Detected Cloudflare protection - may need different approach")
        if 'rate' in response.text.lower() or 'limit' in response.text.lower():
            logger.info("Possible rate limiting detected")
        if 'bot' in response.text.lower() or 'robot' in response.text.lower():
            logger.info("Possible bot detection - will retry with different headers")
            
    def get(self, url: str, 
            headers: Dict[str, str] = None, 
            params: Dict[str, Any] = None,
            allow_redirects: bool = True,
            **kwargs) -> Optional[requests.Response]:
        """
        Enhanced GET request with robust error handling.
        
        Args:
            url: Target URL
            headers: Additional headers (will be merged with random headers)
            params: Query parameters
            allow_redirects: Whether to follow redirects
            **kwargs: Additional arguments passed to requests.get
            
        Returns:
            Response object if successful, None if all retries failed
        """
        return self._make_request('GET', url, headers=headers, params=params, 
                                allow_redirects=allow_redirects, **kwargs)
    
    def post(self, url: str,
             data: Any = None,
             json: Dict[str, Any] = None,
             headers: Dict[str, str] = None,
             **kwargs) -> Optional[requests.Response]:
        """
        Enhanced POST request with robust error handling.
        
        Args:
            url: Target URL
            data: Request body data
            json: JSON data to send
            headers: Additional headers
            **kwargs: Additional arguments passed to requests.post
            
        Returns:
            Response object if successful, None if all retries failed
        """
        return self._make_request('POST', url, data=data, json=json, 
                                headers=headers, **kwargs)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with comprehensive error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Arguments passed to the request method
            
        Returns:
            Response object if successful, None if all retries failed
        """
        headers = kwargs.pop('headers', {})
        
        for attempt in range(self.max_retries + 1):
            try:
                # Generate fresh headers for each attempt
                request_headers = self._get_random_headers(headers)
                
                # Add random delay to avoid being flagged as bot
                if attempt > 0:
                    delay = self.backoff_factor * (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.info(f"Waiting {delay:.2f} seconds before retry {attempt}")
                    time.sleep(delay)
                
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                # Make the request
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Log the response status
                logger.debug(f"Response status: {response.status_code} for {url}")
                
                # Handle different status codes
                if response.status_code == 200:
                    logger.debug(f"Successful request to {url}")
                    return response
                elif response.status_code == 403:
                    self._handle_403_error(response, url, attempt)
                    if attempt == self.max_retries:
                        logger.error(f"Final 403 error for {url} after {self.max_retries + 1} attempts")
                        return response  # Return the 403 response for caller to handle
                elif response.status_code in self.status_forcelist:
                    logger.warning(f"Retryable error {response.status_code} for {url} (attempt {attempt + 1})")
                    if attempt == self.max_retries:
                        logger.error(f"Final error {response.status_code} for {url} after all retries")
                        return response
                else:
                    # For other status codes, return immediately
                    logger.debug(f"Non-retryable status {response.status_code} for {url}")
                    return response
                    
            except (ConnectionError, Timeout) as e:
                logger.warning(f"Network error for {url} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"Final network error for {url}: {e}")
                    return None
            except RequestException as e:
                logger.error(f"Request exception for {url} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"Final request exception for {url}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                return None
        
        return None
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_robust_session(max_retries: int = 3, 
                         backoff_factor: float = 1.0,
                         timeout: int = 30) -> RobustHTTPClient:
    """
    Create a robust HTTP client session.
    
    Args:
        max_retries: Maximum number of retries for failed requests
        backoff_factor: Factor for exponential backoff between retries  
        timeout: Request timeout in seconds
        
    Returns:
        RobustHTTPClient instance
    """
    return RobustHTTPClient(
        max_retries=max_retries,
        backoff_factor=backoff_factor, 
        timeout=timeout
    )


# Convenience functions for backward compatibility
def robust_get(url: str, **kwargs) -> Optional[requests.Response]:
    """Make a robust GET request with default settings."""
    with create_robust_session() as client:
        return client.get(url, **kwargs)


def robust_post(url: str, **kwargs) -> Optional[requests.Response]:
    """Make a robust POST request with default settings.""" 
    with create_robust_session() as client:
        return client.post(url, **kwargs)