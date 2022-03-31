# Change Log

For a list of releases, see: https://github.com/django-ses/django-ses/releases/

## Upcoming (dev)

The following changes are not yet released, but are code complete:

Features:
- None

Changes:
- None

Deprecations:
 - None

Fixes:
- None

## Current

**3.0.0**

Pulls and Issues:
 - https://github.com/django-ses/django-ses/pull/238
   - https://github.com/django-ses/django-ses/issues/232
 - https://github.com/django-ses/django-ses/pull/239
   - https://github.com/django-ses/django-ses/issues/182
   - https://github.com/django-ses/django-ses/issues/176

Features:
 - AWS certificates fetched by the notification verifier are now cached. 
   Previously, each notification that you received and verified would perform 
   an HTTP GET to AWS to download the certificate. This was unnecessary and has
   been replaced with a simple in-memory cache.
 - The repository now uses poetry and a pyproject.toml file for dependency and 
   metadata management. This fixes #232, and lands support for Python 3.10 
   while tidying up a bunch of older Python files (setup.py, manifest.in, and 
   AUTHORS are all removed).
 - The README has been updated and simplified.
 - A new GitHub Action will auto-release tagged commits to PyPi.
 - Verification tests now verify their cryptographic functions against real 
   data and a real certificate.

Changes:
 - The dependency on m2Crypto is removed and is replaced with the
   `cryptography` package. This simplifies the install and moves django-ses to
   a more modern cryptography toolkit. If you previously had installed `SWIG` 
   or `libssl-dev`, those dependencies are no longer needed for this package.

Deprecations:
 - Django 3.0 and 3.1 are deprecated and support for them has been removed.
 - Python 3.5 and 3.6 are deprecated and support for them has been removed.

Fixes:
 - A hang was removed from the notification verifier by adding a `timeout`
   parameter to the certificate download code. Without this timeout, [it was 
   possible](https://github.com/psf/requests/issues/3070) for a broken 
   connection to endlessly hang an application. 

## Past

See: https://github.com/django-ses/django-ses/releases/