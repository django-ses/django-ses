from setuptools import setup, find_packages
import os

DESCRIPTION = "A Django email backend for Amazon's Simple Email Service"

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.rst').read()
except:
    pass

# Dirty hack to get version number from django_ses/__init__.py - we can't
# import it as it depends on boto and boto isn't installed until this
# file is read
init = os.path.join(os.path.dirname(__file__), 'django_ses', '__init__.py')
version_line = filter(lambda l: l.startswith('__version__'), open(init))[0]
version = version_line.split('=')[-1].strip().strip("'")

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Framework :: Django',
]

setup(
    name='django-ses',
    version=version,
    packages=['django_ses'],
    author='Harry Marr',
    author_email='harry@hmarr.com',
    url='http://github.com/hmarr/django-ses/',
    license='MIT',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    install_requires=['boto'],
)
