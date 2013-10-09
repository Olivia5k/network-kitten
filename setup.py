from distutils.core import setup

setup(
    name='kitten',
    version='0.1-dev',
    url='https://github.com/thiderman/kitten',
    author='Lowe Thiderman',
    author_email='lowe.thiderman@gmail.com',
    description=('A decentralized minimalist build system'),
    license='MIT',
    packages=['kitten'],
    scripts=[
        'bin/kitten'
    ],
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
