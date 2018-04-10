import glob
from distutils.core import setup


def find_packages(base_package):
    packages = []
    for filename in glob.iglob(f'{base_package}/**/__init__.py', recursive=True):
        split_filename = filename.split("/")
        package_name = split_filename[0]
        for sub_package in split_filename[1:-1]:
            package_name += f".{sub_package}"
        packages += [package_name]
    return packages

setup(
    name='subatomic_coherence',
    version='0.1.1',
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