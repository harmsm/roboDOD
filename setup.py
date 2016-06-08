#!/usr/bin/env python3

import sys

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Need to add all dependencies to setup as we go!
setup(name='rpyBot',
      packages=find_packages(),
      version='0.3',
      description='Raspberry Py Bot: control a Raspberry Pi robot with python',
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/rpyBot',
      download_url='https://XX',
      zip_safe=False,
      install_requires=["PyCmdMessenger>=0.2.2","RPi.GPIO","tornado"],
      classifiers=[],
      entry_points = {'console_scripts': ['rpyBot = rpyBot.main:main']})

