import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


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
    version='0.2.1',
    url='https://github.com/thiderman/kitten',
    author='Lowe Thiderman',
    author_email='lowe.thiderman@gmail.com',
    description=('A decentralized minimalist build system'),
    license='MIT',
    packages=['kitten'],
    entry_points={
        'console_scripts': [
            'kitten = kitten:main',
        ],
    },
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Clustering',
        'Topic :: System :: Networking',
    ],
)
