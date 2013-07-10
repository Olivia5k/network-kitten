from setuptools import setup

setup(
    name='wolf',
    version='0.1-dev',
    url='https://github.com/thiderman/wolf-python',
    author='Lowe Thiderman',
    author_email='lowe.thiderman@gmail.com',
    description=('A self-propagating peer-to-peer network.'),
    license='BSD',
    entry_points={
        'console_scripts': [
            'wolf = wolf:main'
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
    ],
)
