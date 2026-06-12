"""Custom exceptions for the scraper package.

Each layer raises its own error with a clear message so the caller can
distinguish a network problem from an unsupported site from a parse failure.
"""


class ScraperError(Exception):
    """Base class for all scraper errors."""


class FetchError(ScraperError):
    """Raised when a page cannot be downloaded (network/HTTP failure)."""


class UnsupportedSiteError(ScraperError):
    """Raised when no adapter matches the product URL's host."""


class ParseError(ScraperError):
    """Raised when the adapter's selectors find nothing on the page."""
