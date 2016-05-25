#!/usr/bin/env python3

import sys

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Need to add all dependencies to setup as we go!
setup(name='rpyBot',
      packages=['rpyBot'],
      version='0.3',
      description='RaspberryPyBot: Software for controlling a robot via python (with a javascript frontend)',
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/rpyBot',
      download_url='https://XX',
      zip_safe=False,
      install_requires=["PyCmdMessenger"],
      classifiers=['raspberry pi','robotics','os'],
      entry_points = {'console_scripts': ['rpyBot = rpyBot.rpyBot:main']})

