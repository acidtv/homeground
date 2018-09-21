from setuptools import setup

setup(
    name='housemap',
    packages=['housemap'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'untangle',
        'lxml',
        'flask-sqlalchemy',
        'shapely',
    ],
)
