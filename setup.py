import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

try:
    import kitten
except ImportError:
    kitten = None


install_requires = [
    'Logbook',
    'SQLAlchemy',
    'jsonschema',
    'pyzmq',
    'gevent',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'mock',
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['test', '--cov=kitten']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='kitten',
    version=kitten.version() if kitten else 'unknown',
    url='https://github.com/thiderman/kitten',
    author='Lowe Thiderman',
    author_email='lowe.thiderman@gmail.com',
    description=('A lightweight distributed clustering scheduler'),
    license='MIT',
    packages=['kitten'],
    install_requires=install_requires,
    tests_require=tests_require,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'kitten = kitten:main',
        ],
    },
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2.6',
        'Topic :: System :: Clustering',
        'Topic :: System :: Networking',
    ],
)
