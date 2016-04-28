from setuptools import setup, find_packages

setup(name='python-caseta',
      version='0.1.0',
      description='Access Caseta devices via the Integration API (telnet)',
      url='http://githhub.com/kecorbin/python-caseta',
      author='Kevin Corbin',
      license='MIT',
      install_requires=['requests>=2.0'],
      packages=find_packages(exclude=["dist", "*.test", "*.test.*", "test.*", "test"]),
      zip_safe=True)
