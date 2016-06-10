__description__ = \
"""
Exception definitions for rpyBot package.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-25"

class BotError(Exception):
    """
    Base class for all other package-specific exceptions.
    """
    
    pass

class BotOwnershipError(BotError):
    """
    Exception raised when two pieces of code are trying to access same piece 
    of hardware simultaneously.
    """

    pass

class BotEmergencyError(BotError):
    """
    Exception for some error state that is so bad the bot should (probably) be
    dead-stopped.
    """

    pass

class BotConfigurationError(BotError):
    """
    Exception for some problem with the user's configuration of the system.
    """

    pass

class BotMessageError(BotError):
    """
    Exception for a messed up message of some sort.
    """

    pass
