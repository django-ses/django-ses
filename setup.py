from setuptools import setup, find_packages
import os

DESCRIPTION = "A Django email backend for Amazon's Simple Email Service"

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.rst').read()
except:
    pass

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
    version=__import__('django_ses').__version__,
    packages=['django_ses'],
    author='Harry Marr',
    author_email='harry@hmarr.com',
    url='http://github.com/hmarr/django-ses/',
    license='MIT',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    install_requires=['django', 'boto'],
)
