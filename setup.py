from distutils.core import setup
import versioneer
versioneer.versionfile_source = 'kitten/_version.py'
versioneer.versionfile_build = '_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'kitten-'  # dirname like 'kitten-1.2.0'


setup(
    name='kitten',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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
