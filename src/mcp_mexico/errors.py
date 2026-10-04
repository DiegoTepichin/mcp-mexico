class McpMexicoError(Exception):
    """An anticipated failure whose message is safe and useful to show to the model."""


class DataNotAvailableError(McpMexicoError, LookupError):
    """The requested period is not covered by the data this server ships or can reach."""


class InvalidRequestError(McpMexicoError, ValueError):
    """The arguments are well typed but do not make sense together (e.g. start after end)."""


class MissingTokenError(McpMexicoError):
    """A required API token is not configured."""


class UpstreamError(McpMexicoError):
    """An official API failed, rejected the request or could not be reached."""
