"""Error handling utilities with retry logic for AWS operations."""

import time
import logging
from typing import Callable, Optional, TypeVar
from functools import wraps
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.exceptions import EndpointConnectionError, ReadTimeoutError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Optional[Callable[..., T]] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_exceptions: tuple = (ClientError, ReadTimeoutError, EndpointConnectionError),
) -> Callable[..., Optional[T]]:
    """
    Decorator to retry functions with exponential backoff.

    Args:
        func: Function to decorate (optional when used with parameters)
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_exceptions: Tuple of exceptions to catch and retry

    Returns:
        Wrapped function with retry logic
    """

    def decorator(f: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Optional[T]:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {f.__name__}: {e}"
                    )

                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {delay:.2f}s...")
                        time.sleep(min(delay, max_delay))
                        delay *= 2  # Exponential backoff

            logger.error(f"All {max_retries} attempts failed for {f.__name__}")
            raise last_exception

        return wrapper

    # Support both @retry and @retry(max_retries=5) syntax
    if func is not None:
        return decorator(func)
    return decorator


def handle_aws_errors(func: Callable[..., T]) -> Callable[..., Optional[T]]:
    """
    Decorator to handle common AWS errors gracefully.

    Catches:
    - NoCredentialsError: Missing AWS credentials
    - ClientError: AWS service errors
    - EndpointConnectionError: Network issues
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return None
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"AWS ClientError ({error_code}): {e}")
            return None
        except EndpointConnectionError:
            logger.error("Could not connect to AWS endpoint")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            return None

    return wrapper


def validate_boto3_response(response: dict, expected_keys: list = None) -> bool:
    """
    Validate a boto3 response contains expected keys.

    Args:
        response: The boto3 response dictionary
        expected_keys: List of keys that should be present

    Returns:
        True if validation passed, False otherwise
    """
    if not response:
        return False

    if expected_keys:
        missing = [key for key in expected_keys if key not in response]
        if missing:
            logger.warning(f"Missing expected keys: {missing}")
            return False

    return True


class RateLimiter:
    """
    Simple rate limiter for AWS API calls.

    Prevents hitting service quotas and throttling.
    """

    def __init__(self, requests_per_second: float = 10.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_call = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        current = time.time()
        elapsed = current - self.last_call

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: waiting {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_call = time.time()


# Example usage
if __name__ == "__main__":

    @retry_with_backoff(max_retries=3)
    def sample_aws_call():
        """Simulated AWS API call."""
        import random

        if random.random() < 0.7:  # 70% failure rate for demo
            raise ClientError({"Error": {"Code": "Throttling"}}, "TestOperation")
        return "Success!"

    @handle_aws_errors
    def safe_aws_call():
        """AWS call with error handling."""
        return "AWS Operation Result"

    print("Testing retry decorator...")
    result = sample_aws_call()
    print(f"Result: {result}")

    print("\nTesting error handler...")
    result = safe_aws_call()
    print(f"Result: {result}")
