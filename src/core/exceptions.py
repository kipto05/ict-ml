
class ICTBotException(Exception):
    """Base exception for ICT Trading Bot."""
    pass


class MT5ConnectionError(ICTBotException):
    """MT5 connection related errors."""
    pass


class MT5ExecutionError(ICTBotException):
    """MT5 order execution errors."""
    pass


class DataError(ICTBotException):
    """Data processing errors."""
    pass


class StructureDetectionError(ICTBotException):
    """Market structure detection errors."""
    pass


class MLModelError(ICTBotException):
    """Machine learning model errors."""
    pass


class RiskManagementError(ICTBotException):
    """Risk management violations."""
    pass


class ConfigurationError(ICTBotException):
    """Configuration errors."""
    pass


class ValidationError(ICTBotException):
    """Data validation errors."""
    pass