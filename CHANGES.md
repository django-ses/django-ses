# Change Log

For a list of releases, see: https://github.com/django-ses/django-ses/releases/

## Upcoming (dev)

The following changes are not yet released, but are code complete:

Pulls and Issues:
 - None

Features:
- None

Changes:
- None

Deprecations:
 - None

Fixes:
- None

## Current

**4.1.0**

Adds support for AWS Session Profile with a new setting.

This is a minor bump due to the new setting, it also changes the way the
connection is initialized, see [here](https://github.com/django-ses/django-ses/pull/323/files#diff-0cbba929f061bb8c1faa375bac96beeb00879395919333f2c0a0791e8a9265a7R109).


Pulls:
  - https://github.com/django-ses/django-ses/pull/323

Issues:

  - https://github.com/django-ses/django-ses/issues/322


## Past

**4.0.0**

Drops support for Django 2 and python 3.7

Pulls:
  - https://github.com/django-ses/django-ses/pull/318
  - https://github.com/django-ses/django-ses/pull/321

**3.6.0**

Fixes unicode surrogate issues from 3.11.9 and 3.12.3

Pulls:
  - https://github.com/django-ses/django-ses/pull/316

Issues:

  - https://github.com/django-ses/django-ses/issues/315

**3.5.1/3.5.2**

Double release because the wrong commit was tagged, sorry.

Pulls:
  - https://github.com/django-ses/django-ses/pull/281
  - https://github.com/django-ses/django-ses/pull/291
  - https://github.com/django-ses/django-ses/pull/289
  - https://github.com/django-ses/django-ses/pull/284


**3.5.0**

Pulls:
  - https://github.com/django-ses/django-ses/pull/284

Fixes:
  - Security issue in certificate domain validation, see https://github.com/django-ses/django-ses/security/advisories/GHSA-qg36-9jxh-fj25

**3.4.1**

Pulls:
  - https://github.com/django-ses/django-ses/pull/279

Fixes:
  - https://github.com/django-ses/django-ses/issues/278
  - Fix for: "Invalid type for parameter FeedbackForwardingEmailAddress, value: None"

**3.4.0**

Pulls:
  - https://github.com/django-ses/django-ses/pull/276

Fixes:
  - BREAKING CHANGE: New behavior of `AWS_SES_RETURN_PATH` to only be used for bounces/returns.
  - Add `AWS_SES_FROM_EMAIL` to use as `from` address.
  - See https://github.com/django-ses/django-ses/pull/276/files#r1169200001 for example.

**3.3.0**

Pulls:
  - https://github.com/django-ses/django-ses/pull/267
  - https://github.com/django-ses/django-ses/pull/269

Fixes:
  - Support of SESv2 client. Fixes #229.

**3.2.2**

Pulls:
  - https://github.com/django-ses/django-ses/pull/263

Fixes:
  - Support newer versions of cryptography (loosen required version)
    Fixes #262.

**3.2.1**

Pulls:
  - https://github.com/django-ses/django-ses/pull/264

Fixes:
  - Support different versions of requests (loosen required version)
    Fixes #262. See also #263.

**3.2.0**

Pulls:
  - https://github.com/django-ses/django-ses/pull/259

Fixes:
  - Use eventType and fall back to notificationType consistently for SES events.
    Fixes #174.


**3.1.2**

Pulls:
  - https://github.com/django-ses/django-ses/pull/255
  - https://github.com/django-ses/django-ses/pull/254
  - https://github.com/django-ses/django-ses/pull/252
  - https://github.com/django-ses/django-ses/pull/246


Features:
  - Upgrade importlib-metadata

**3.1.0**

Pulls:
  - https://github.com/django-ses/django-ses/pull/250

Features:
  - Add support for temporary AWS credentials using session token.

**3.0.1**

Pulls:
 - https://github.com/django-ses/django-ses/issues/242

Fixes:
 - Ensures that notification verification works even when notifications lack
   certain fields.

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

## Distant Past

See: https://github.com/django-ses/django-ses/releases/
