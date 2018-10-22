# `py2api`

Expose python objects to external clients with minimal effort.

## Virtual Environments

### `pip-compile-multi`

Python dependencies are managed using
[`pip-compile-multi`][pip-compile-multi]. This builds several
different [`requirements.txt`][requirements] files that can include
common requirements.

### Creating the Environment

To create a [`virtualenv`][virtualenv] that any of the
[`requirements`][requirements] can be installed to, run:

    virtualenv venv
    . ./venv/activate

### Developing

After creating a base [`virtualenv`][virtualenv], you can create
a development environment including [hypothesis][hypothesis] and
[IPython][ipython] by running:

    pip install -Ur requirements/develop.txt

### Testing

If you just want to run tests, you can create a testing environment
which only includes [hypothesis][hypothesis] by running:

    pip install -Ur requirements/test.txt

## Tests

Once any of the testing [`virtualenv`s][virtualenv] have been set up,
you can run tests with:

    pytest

[pip-compile-multi]: https://pypi.org/project/pip-compile-multi/ "`pip-compile-multi`"

[requirements]: https://pip.readthedocs.io/en/1.1/requirements.html "`requirements.txt`"

[virtualenv]: https://virtualenv.pypa.io/en/stable/ "`virtualenv`"

[hypothesis]: https://hypothesis.readthedocs.io/en/latest/ "hypothesis"

[ipython]: https://ipython.readthedocs.io/en/stable/ "IPython"
