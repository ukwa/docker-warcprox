#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='warcprox-plugins',
      version='1.0',
      description='Python Distribution Utilities',
      author='Greg Ward',
      author_email='gward@python.net',
      url='https://www.python.org/sigs/distutils-sig/',
      packages=['warcprox-plugins'],
      install_requires=[
          "warcprox",
          "kafka-python",
          "requests"
      ],
      dependency_links=[
          "git+https://github.com/internetarchive/warcprox.git#egg=warcprox"
      ]
      )
