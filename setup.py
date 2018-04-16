import glob
from distutils.core import setup
import sys
import time

version_base = '0.1.2'
version_modifier = ''


def find_packages(base_package):
    packages = []
    for filename in glob.iglob(f'{base_package}/**/__init__.py', recursive=True):
        split_filename = filename.split("/")
        package_name = split_filename[0]
        for sub_package in split_filename[1:-1]:
            package_name += f".{sub_package}"
        packages += [package_name]
    return packages

if "--test" in sys.argv:
    sys.argv.remove("--test")
    version_modifier = "-" + str(int(round(time.time() * 1000)))

setup(
    name='subatomic_coherence',
    version=version_base + version_modifier,
    packages=find_packages("subatomic_coherence"),
    url='https://github.com/absa-subatomic/subatomic_coherence',
    license='Apache License 2.0',
    description='A Slack integration testing framework',
    install_requires=[
          'colorama',
          'requests',
          'slackclient',
      ]
)