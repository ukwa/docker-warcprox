#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='warcprox-plugins',
      version='2.4.17',
      description='Extending warcprox with UKWA plugins',
      author='Andrew Jackson',
      author_email='andrew.jackson@bl.uk',
      url='https://www.github.com/ukwa/docker-warcprox/',
      packages=['warcprox-plugins'],
      install_requires=[
          "warcprox==2.4.17",
          "kafka-python",
          "requests"
      ]
      )
