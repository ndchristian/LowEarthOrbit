from distutils.core import setup

setup(
    name='LowEarthOrbit',
    version='0.1dev',
    author='Nicholas Christian',
    author_email='ndchristian@gmail.com',
    packages=['lowearthorbit'],
    license='LICENSE.txt',
    description='A better way to deploy AWS Cloudformation',
    long_description=open('README.txt').read()
)