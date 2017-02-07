from setuptools import setup, find_packages

setup(
    name='stackcollector',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests>=2.4.3',
        'flask>=0.10.1',
        'click',
        'dateparser'
    ],
)
