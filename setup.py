# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from setuptools import setup, find_packages

SHORT_DESCRIPTION = 'A tool for validating stackdio formulas.'

# Grab README.md and use its contents as the long description
with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

requirements = [
    'click>=6',
    'PyYAML>=3.10',
    'salt>=2015.8.8,<2015.9',
]

# Call the setup method from setuptools that does all the heavy lifting
# of packaging stackdio
setup(
    name='stackdio-formula-validator',
    version='0.7.0.dev',
    url='http://stackd.io',
    author='Digital Reasoning Systems, Inc.',
    author_email='info@stackd.io',
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license='Apache 2.0',
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'dist', 'build', 'docs')),
    zip_safe=False,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
    ],
    entry_points={
        'console_scripts': [
            'validate-formula = stackdio.validator:main',
        ],
    }
)
