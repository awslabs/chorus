---
title: Installation
nextjs:
  metadata:
    title: Installation
    description: Learn how to install Chorus on your system and set up your development environment.
---

This guide will help you install Chorus and its dependencies on your system. Chorus is available as a Python package through PyPI or directly from the GitHub repository.

---

## Prerequisites

Before installing Chorus, ensure you have the following prerequisites:

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended) - venv, conda, or similar

{% callout type="note" title="Note" %}
We recommend using a virtual environment for your Chorus projects to avoid dependency conflicts with other Python applications.
{% /callout %}

## Standard Installation

The simplest way to install Chorus is through pip, which will install the latest stable release from PyPI.

```bash
pip install python-chorus
```

To verify the installation, run:

```bash
python -c "import chorus; print(chorus.__version__)"
```

This should print the version of Chorus that you have installed.

## Installing with Dependencies

Chorus offers additional dependency groups for different use cases:

### Basic Dependencies

```bash
pip install python-chorus
```

### With All Optional Dependencies

```bash
pip install "python-chorus[all]"
```

### With Specific Feature Dependencies

```bash
# For development tools
pip install "python-chorus[dev]"

# For testing tools
pip install "python-chorus[test]"

# For OpenAI integration
pip install "python-chorus[openai]"

# For LangChain integration
pip install "python-chorus[langchain]"

# For JSONNet template support
pip install "python-chorus[jsonnet]"

# For multiple optional dependencies
pip install "python-chorus[langchain,jsonnet,openai]"
```

You can also install Chorus with specific versions of these dependencies:

```bash
# Install with a specific version of OpenAI
pip install "python-chorus[openai]" "openai>=1.0.0"

# Install with a specific version of LangChain
pip install "python-chorus[langchain]" "langchain>=0.1.0"

# Install with a specific version of JSONNet
pip install "python-chorus[jsonnet]" "jsonnet>=0.20.0"
```

---

## Installing Nightly Builds

If you want to use the latest features and improvements before they're released in a stable version, you can install the development version directly from GitHub.

### From GitHub Nightly Branch

```bash
pip install git+https://github.com/awslabs/chorus.git@nightly
```

### From a Specific Branch or Commit

```bash
# From the main branch
pip install git+https://github.com/awslabs/chorus.git@main

# From a feature branch
pip install git+https://github.com/awslabs/chorus.git@feature-branch-name

# From a specific commit
pip install git+https://github.com/awslabs/chorus.git@commit-hash
```

{% callout type="warning" title="Warning" %}
Nightly builds may contain experimental features and could have bugs or breaking changes. We recommend using these only for testing or development purposes, not for production environments.
{% /callout %}

---

## Development Installation

If you plan to contribute to Chorus or want to modify the source code, you can install it in development mode:

1. Clone the repository:
   ```bash
   git clone https://github.com/awslabs/chorus.git
   cd chorus
   ```

2. Install in development mode:
   ```bash
   pip install -e ".[dev,test]"
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   pre-commit install
   ```

---

## Troubleshooting

### Common Installation Issues

#### Dependency Conflicts

If you encounter dependency conflicts, try installing Chorus in a clean virtual environment:

```bash
python -m venv chorus-env
source chorus-env/bin/activate  # On Windows, use: chorus-env\Scripts\activate
pip install python-chorus
```

#### Permission Errors

If you get permission errors during installation, try using the `--user` flag:

```bash
pip install --user python-chorus
```

Or use a virtual environment as described above.

### Getting Help

If you encounter any issues that aren't covered here, please:

1. Check the [GitHub Issues](https://github.com/awslabs/chorus/issues) for known problems
2. Open a new issue if you've found a bug

---

## Next Steps

Now that you have Chorus installed, you're ready to start building your first multi-agent system! Check out our [Hello World tutorial](/docs/hello-world) to create your first Chorus application in minutes.
