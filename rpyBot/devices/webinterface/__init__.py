__description__ = \
"""
Device that creates a tornado webserver/socket that can be connected to over
http to provide a remote interface for the robot.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-06-09"

__all__ = ["webinterface"]

from .webinterface import WebInterfaceDevice
