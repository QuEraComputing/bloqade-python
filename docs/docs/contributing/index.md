# Contributing

## How to contribute

## Setup development environment

We use [pdm](https://pdm.fming.dev/) to manage dependencies and virtual environment.
After cloning the repository, run the following command to install dependencies:

```bash
pdm install
```

You can also install different dependency groups:

- **dev**: dependencies for development

```bash
pdm install --dev
# or
pdm install -d
```

- **doc**: dependencies for building documentation

```bash
pdm install -G doc
```

## Useful PDM scripts

### Tests

You can run tests via

```bash
pdm run test
```

Or run tests and generate coverage via

```bash
pdm run coverage
```

### Documentation

You can build documentation via

```bash
pdm run doc_build
```

Or run a local server to preview documentation via

```bash
pdm run doc
```

### Jupytext

You can sync jupyter notebooks and python scripts via

```bash
pdm run jupytext
```

this will help you development examples in jupyter notebook and python scripts simultaneously.

## Lint

We primarily use [ruff](https://github.com/charliermarsh/ruff) - an extremely fast linter for Python, and
[black](https://github.com/psf/black) as formatter. These has been configured into [pre-commit](https://pre-commit.com/) hooks. You can install pre-commit hooks to git via

```bash
pre-commit install
```
