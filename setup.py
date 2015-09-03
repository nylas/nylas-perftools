from setuptools import setup, find_packages

setup(
    name='stackcollector',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'influxdb',
        'flask'
    ],
    data_files=[('stackcollector', ['flamegraph.pl'])]
)
