from setuptools import setup

setup(
    name='housemap',
    packages=['housemap'],
    include_package_data=True,
    install_requires=[
        'flask',
        'lxml',
        'sqlalchemy',
        'flask-sqlalchemy',
        'shapely',
        'utm',
    ],
)
