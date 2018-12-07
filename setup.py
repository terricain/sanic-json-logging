#!/usr/bin/env python3
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='sanic-json-logging',
    version='1.1.0',
    description="Simple library to emit json formatted logs to stdout",
    long_description=readme,
    author="Terry Cain",
    author_email='terry@terrys-home.co.uk',
    url='https://github.com/terrycain/sanic-json-logging',
    packages=find_packages(include=['sanic_json_logging*']),
    include_package_data=True,
    install_requires=['sanic>=0.8.3'],
    license="Apache 2",
    zip_safe=False,
    keywords='sanic json logging',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests'
)
