import pprint
import versioneer
import setuptools
import os.path

PACKAGE = "cassandra_lwt_migration_tool"
HOMEPAGE = 'https://github.com/backblaze/cassandra_lwt_migration_tool'
PYTHON_REQUIRES = '3.8'

REQUIREMENTS = ["cassandra-driver~=3.25"]
DEV_REQUIREMENTS = []


def relative_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


SETUP_ARGS = dict(
    name=PACKAGE,
    author='Backblaze',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url=HOMEPAGE,
    description="Tool to help resolve Cassandra LWTs during large topology changes.",
    long_description=open(relative_filename('README.md')).read().strip(),
    python_requires=f'~={PYTHON_REQUIRES}',
    install_requires=REQUIREMENTS,
    extras_require={'dev': DEV_REQUIREMENTS},
    entry_points={
        "console_scripts": ["cassandra_lwt_migration_tool = cassandra_lwt_migration_tool.__main__:main"]
    },
    packages=setuptools.find_packages(exclude='tests')
)

pprint.pprint(SETUP_ARGS)
setuptools.setup(**SETUP_ARGS)