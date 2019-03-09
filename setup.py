# -*- coding: utf-8 -*-
# Copyright (c) 2018 Luca Pinello
# Made available under the MIT license.


#This is based on: https://github.com/Roastero/freshroastsr700

import os
from setuptools import setup
from setuptools import find_packages


here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='freshroastsr700_phidget',
    version=1.1,
    description='An extended Python module to control a FreshRoastSR700 coffee roaster using a Phidget Temperature Sensor',
    url='https://github.com/lucapinello/freshroastsr700_phidget',
    author='Luca Pinello',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'pyserial>=3.0.1',
        'Phidget22', #you need the version from the Phidget website
        'freshroastsr700>=0.2.1',
    ]
)
