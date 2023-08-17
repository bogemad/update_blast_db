from setuptools import setup, find_packages

setup(
    name='update_blast_db',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests'
    ],
    scripts=['bin/update_blast_db'],
)
