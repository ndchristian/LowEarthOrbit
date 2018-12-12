import setuptools
from distutils.core import setup

setup(
    name='LowEarthOrbit',
    version='0.6.6',
    author='Nicholas Christian',
    author_email='ndchristian@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    license='LICENSE.txt',
    description='A better way to deploy AWS CloudFormation',
    long_description=open('README.txt').read(),
    install_requires=['click',
                      'botocore',
                      'boto3'
                      ],
    entry_points={
        'console_scripts': [
            'leo = lowearthorbit.leo:cli'
        ]
    },
)
