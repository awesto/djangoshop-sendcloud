#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from setuptools import setup, find_packages
from shop_sendcloud import __version__

with open('README.md', 'r') as fh:
    long_description = fh.read()

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
]

setup(
    author="Jacob Rief",
    author_email="jacob.rief@gmail.com",
    name='djangoshop-sendcloud',
    version=__version__,
    description='SendCloud Shipping Provider Integration for django-shop',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jrief/djangoshop-sendcloud',
    license='MIT License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'requests',
        'django-phonenumber-field',
        'phonenumbers',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
