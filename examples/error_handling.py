"""
Error handling examples for the Elfa Python SDK

This example demonstrates proper error handling techniques and how to
gracefully handle various error scenarios that may occur when using the API.

Requirements:
- Set ELFA_API_KEY environment variable with your API key
- Install the SDK: pip install elfa-ai
"""

import os
import time

from elfa import ElfaClient
from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaTimeoutError,
    ElfaValidationError,
)


def demonstrate_authentication_error():
    """Show how to handle authentication errors"""
    print("🔑 Testing authentication error handling...")

    # Use an invalid API key
    client = ElfaClient(api_key="invalid-api-key-12345")

    try:
        response = client.ping()
        print("❌ This should not happen - ping with invalid key succeeded")
    except ElfaAuthenticationError as e:
        print(f"✅ Caught authentication error as expected: {e}")
        print(f"   Status code: {e.status_code}")
        print(f"   Message: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error type: {type(e).__name__}: {e}")
    finally:
        client.close()
    print()


def demonstrate_validation_error():
    """Show how to handle validation errors"""
    print("⚠️ Testing validation error handling...")

    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("⏭️ Skipping validation test - no API key provided")
        return

    client = ElfaClient(api_key=api_key)

    try:
        # Try to call keyword mentions without keywords or account name
        response = client.get_keyword_mentions()
        print("❌ This should not happen - empty search succeeded")
    except ValueError as e:
        print(f"✅ Caught validation error as expected: {e}")
    except ElfaValidationError as e:
        print(f"✅ Caught API validation error: {e}")
        if e.validation_errors:
            print(f"   Validation details: {e.validation_errors}")
    except Exception as e:
        print(f"❌ Unexpected error type: {type(e).__name__}: {e}")
    finally:
        client.close()
    print()


def demonstrate_rate_limit_handling():
    """Show how to handle rate limiting"""
    print("🚦 Testing rate limit handling...")

    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("⏭️ Skipping rate limit test - no API key provided")
        return

    client = ElfaClient(api_key=api_key, max_retries=2)

    try:
        # Check current API status first
        status = client.get_api_key_status()
        print(
            f"📊 Current usage: {status.data.usage.today}/{status.data.daily_limit} daily"
        )

        # Make several requests quickly to potentially hit rate limits
        print("🔄 Making rapid API calls to test rate limiting...")
        for i in range(5):
            try:
                trending = client.get_trending_tokens(page_size=10)
                print(f"   Request {i+1}: ✅ {len(trending.data.data)} tokens")
                time.sleep(0.1)  # Small delay to avoid overwhelming
            except ElfaRateLimitError as e:
                print(f"   Request {i+1}: 🚦 Rate limited!")
                print(f"   Retry after: {e.retry_after} seconds")
                print(f"   Limit type: {e.limit_type}")

                if e.retry_after:
                    print(f"   Waiting {e.retry_after} seconds before retrying...")
                    time.sleep(e.retry_after)
                    # Retry the request
                    try:
                        trending = client.get_trending_tokens(page_size=10)
                        print(f"   Retry: ✅ {len(trending.data.data)} tokens")
                    except Exception as retry_error:
                        print(f"   Retry failed: {retry_error}")
                break

    except ElfaRateLimitError as e:
        print(f"✅ Caught rate limit error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
    finally:
        client.close()
    print()


def demonstrate_network_error_handling():
    """Show how to handle network errors"""
    print("🌐 Testing network error handling...")

    # Use an invalid base URL to simulate network issues
    client = ElfaClient(
        api_key="test-key",
        base_url="https://invalid-url-that-does-not-exist.com",
        timeout=5.0,
        max_retries=2,
    )

    try:
        response = client.ping()
        print("❌ This should not happen - invalid URL succeeded")
    except ElfaNetworkError as e:
        print(f"✅ Caught network error as expected: {e}")
        if e.original_error:
            print(f"   Original error: {type(e.original_error).__name__}")
    except ElfaTimeoutError as e:
        print(f"✅ Caught timeout error as expected: {e}")
    except Exception as e:
        print(f"❌ Unexpected error type: {type(e).__name__}: {e}")
    finally:
        client.close()
    print()


def demonstrate_comprehensive_error_handling():
    """Show comprehensive error handling in a real scenario"""
    print("🛡️ Comprehensive error handling example...")

    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("⏭️ Skipping comprehensive test - no API key provided")
        return

    client = ElfaClient(api_key=api_key)

    # Define operations to test
    operations = [
        ("Health Check", lambda: client.ping()),
        ("API Status", lambda: client.get_api_key_status()),
        ("Trending Tokens", lambda: client.get_trending_tokens(time_window="24h")),
        (
            "Bitcoin Mentions",
            lambda: client.get_keyword_mentions(keywords="bitcoin", limit=5),
        ),
        (
            "Invalid Account Stats",
            lambda: client.get_account_smart_stats(username="nonexistent_user_12345"),
        ),
    ]

    results = {"success": 0, "errors": 0, "details": []}

    for operation_name, operation in operations:
        try:
            print(f"🔄 Executing: {operation_name}")
            result = operation()
            print(f"   ✅ Success")
            results["success"] += 1
            results["details"].append(f"{operation_name}: Success")

        except ElfaAuthenticationError as e:
            print(f"   🔑 Authentication error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Auth error")

        except ElfaRateLimitError as e:
            print(f"   🚦 Rate limit error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Rate limited")

        except ElfaValidationError as e:
            print(f"   ⚠️ Validation error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Validation error")

        except ElfaNotFoundError as e:
            print(f"   🔍 Not found error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Not found")

        except ElfaNetworkError as e:
            print(f"   🌐 Network error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Network error")

        except ElfaTimeoutError as e:
            print(f"   ⏰ Timeout error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Timeout")

        except ElfaAPIError as e:
            print(f"   ❌ General API error: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: API error")

        except Exception as e:
            print(f"   💥 Unexpected error: {type(e).__name__}: {e}")
            results["errors"] += 1
            results["details"].append(f"{operation_name}: Unexpected error")

    print(f"\n📊 Results Summary:")
    print(f"   ✅ Successful operations: {results['success']}")
    print(f"   ❌ Failed operations: {results['errors']}")
    print(f"   📋 Details:")
    for detail in results["details"]:
        print(f"      • {detail}")

    client.close()
    print()


def demonstrate_retry_logic():
    """Show how the retry logic works"""
    print("🔄 Testing retry logic...")

    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("⏭️ Skipping retry test - no API key provided")
        return

    # Create client with custom retry settings
    client = ElfaClient(api_key=api_key, max_retries=3, retry_delay=1.0)

    try:
        print("🔄 Making API call with retry logic enabled...")
        start_time = time.time()

        # This should succeed normally
        response = client.get_trending_tokens(page_size=5)

        end_time = time.time()
        print(f"✅ Request completed in {end_time - start_time:.2f} seconds")
        print(f"   Found {len(response.data.data)} trending tokens")

    except Exception as e:
        print(f"❌ Request failed after retries: {e}")
    finally:
        client.close()
    print()


def main():
    """Run all error handling demonstrations"""
    print("🛡️ Elfa SDK Error Handling Examples")
    print("=" * 50)

    # Run all demonstrations
    demonstrate_authentication_error()
    demonstrate_validation_error()
    demonstrate_rate_limit_handling()
    demonstrate_network_error_handling()
    demonstrate_retry_logic()
    demonstrate_comprehensive_error_handling()

    print("✅ Error handling examples completed!")
    print("\n💡 Key takeaways:")
    print("   • Always use specific exception types for better error handling")
    print("   • Check API key status to monitor usage and avoid rate limits")
    print("   • Implement retry logic for transient network issues")
    print("   • Use timeouts to prevent hanging requests")
    print("   • Log errors appropriately for debugging and monitoring")


if __name__ == "__main__":
    main()
