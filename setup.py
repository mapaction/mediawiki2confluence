"""m2c: A bespoke MediaWiki to Confluence migration tool."""

from setuptools import find_packages, setup

dependencies = ['click', 'mwclient', 'pypandoc',
                'panflute', 'beautifulsoup4', 'requests']

setup(
    name='m2c',
    version='0.0.1',
    url='https://github.com/mapaction/mediawiki2confluence',
    license='GPLv3',
    author='Aptivate Cooperators',
    author_email='tech@aptivate.org',
    description='A bespoke MediaWiki to Confluence migration tool.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'm2c = m2c.cli:main',
        ],
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
    ]
)
