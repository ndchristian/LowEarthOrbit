from distutils.core import setup

setup(
    name='LowEarthOrbit',
    version='0.2dev',
    author='Nicholas Christian',
    author_email='ndchristian@gmail.com',
    packages=['lowearthorbit'],
    license='LICENSE.txt',
    description='A better way to deploy AWS Cloudformation',
    long_description=open('README.txt').read(),
    install_requires=['Click',
                      'botocore',
                      'boto3'
                      ],
    entry_points='''
    [console_scripts]
    leo=leo:cli
    '''
)