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

class BotOwnershipError(Exception):
    """
    Exception raised when two pieces of code are trying to access same piece 
    of hardware simultaneously.
    """

    pass

class BotEmergencyError(Exception):
    """
    Exception for some error state that is so bad the bot should (probably) be
    dead-stopped.
    """

    pass

class BotConfigurationError(Exception):
    """
    Exception for some problem with the user's configuration of the system.
    """

    pass
