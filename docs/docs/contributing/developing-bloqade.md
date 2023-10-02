# Setting up your Development Environment

!!! tip "Before You Get Started"

    Depending on the complexity of the contribution you'd like to make to 
    Bloqade, it may be worth reading the [Design Philosophy and Architecture](design-philosophy-and-architecture.md)
    section to get an idea of why Bloqade is structured the way that it is and 
    how to make your contribution adhere to this philosophy.

Our development environment contains a set of tools we use
for development, testing, and documentation. This section
describes how to set up the development environment. We primarily
use [pdm](https://pdm.fming.dev/) to manage python environments
and dependencies.

## Setting up Python

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

will print out the coverage file level report in terminal.

```bash
pdm run coverage-html
```

This command generates an interactive html report in `htmlcov` folder.
This will show which specific lines are not covered by tests.

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
[black](https://github.com/psf/black) as formatter. These have been configured into [pre-commit](https://pre-commit.com/) hooks. After installing pre-commit on your own system, you can install pre-commit hooks to git via

```bash
pre-commit install
```
