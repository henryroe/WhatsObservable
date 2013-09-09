from setuptools import setup

setup(name='WhatsObservable',
      version='0.1.0',
      description='Determine which small solar system bodies are observable from a given location at a given time',
      long_description=open('README.txt').read(),
      author='Henry Roe',
      author_email='hroe@hroe.me',
      url='http://github.com/henryroe/WhatsObservable',
      license='LICENSE.txt',
      py_modules=['whatsobservable'],
      install_requires=['pandas>=0.10.1', 'pyephem>=3.7.5.1'])
