========
Overview
========

Alignment prhe MOUSE X-ray scattering instrument at BAM to study thin films.

.. start-badges

| |version| |commits-since| |license|
| |supported-versions| |wheel| |downloads|
| |cicd| |coverage|

.. |version| image:: https://img.shields.io/pypi/v/mouse-alignment-routines.svg
    :target: https://test.pypi.org/project/mouse-alignment-routines
    :alt: PyPI Package latest release

.. |commits-since| image:: https://img.shields.io/github/commits-since/BAMresearch/mouse-alignment-routines/v0.1.0.svg
    :target: https://github.com/BAMresearch/mouse-alignment-routines/compare/v0.1.0...main
    :alt: Commits since latest release

.. |license| image:: https://img.shields.io/pypi/l/mouse-alignment-routines.svg
    :target: https://en.wikipedia.org/wiki/GNU_General_Public_License
    :alt: License

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/mouse-alignment-routines.svg
    :target: https://test.pypi.org/project/mouse-alignment-routines
    :alt: Supported versions

.. |wheel| image:: https://img.shields.io/pypi/wheel/mouse-alignment-routines.svg
    :target: https://test.pypi.org/project/mouse-alignment-routines#files
    :alt: PyPI Wheel

.. |downloads| image:: https://img.shields.io/pypi/dw/mouse-alignment-routines.svg
    :target: https://test.pypi.org/project/mouse-alignment-routines/
    :alt: Weekly PyPI downloads

.. |cicd| image:: https://github.com/BAMresearch/mouse-alignment-routines/actions/workflows/ci-cd.yml/badge.svg
    :target: https://github.com/BAMresearch/mouse-alignment-routines/actions/workflows/ci-cd.yml
    :alt: Continuous Integration and Deployment Status

.. |coverage| image:: https://img.shields.io/endpoint?url=https://BAMresearch.github.io/mouse-alignment-routines/coverage-report/cov.json
    :target: https://BAMresearch.github.io/mouse-alignment-routines/coverage-report/
    :alt: Coverage report

.. end-badges


Installation
============

::

    pip install mouse-alignment-routines

You can also install the in-development version with::

    pip install git+https://github.com/BAMresearch/mouse-alignment-routines.git@main


Documentation
=============

https://BAMresearch.github.io/mouse-alignment-routines

Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
