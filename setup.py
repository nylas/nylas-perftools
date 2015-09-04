from setuptools import setup, find_packages

setup(
    name='stackcollector',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests>=2.4.3',
        'flask>=0.10.1',
        'flask-sqlalchemy>=2.0',
        'psycopg2>=2.6.1',
        'nylas-production-python>=0.2.3'
    ],
)
