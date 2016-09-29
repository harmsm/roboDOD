#!/usr/bin/env python3

import sys, os

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Figure out non-python files to include for client
client_files = []
for root, dirs, files in os.walk("client"):
    for file in files:
        client_files.append(os.path.join(root,file))

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
      install_requires=["PyCmdMessenger>=0.2.2","tornado"], #RPi.GPIO","tornado"],
      classifiers=[],
      entry_points = {'console_scripts': ['rpyBot = rpyBot.main:main']},
      package_data={'': client_files})

