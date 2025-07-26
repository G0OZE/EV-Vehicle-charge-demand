"""
Setup script for AICTE Workflow Tool
"""
from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version from __init__.py
def get_version():
    version_file = os.path.join("src", "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="aicte-workflow-tool",
    version=get_version(),
    author="AICTE Workflow Tool Team",
    author_email="killerfantom23@gmail.com",
    description="Automation tool for AICTE internship project workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/G0OZE/EV-Vehicle-charge-demand",
    project_urls={
        "Bug Tracker": "https://github.com/G0OZE/EV-Vehicle-charge-demand/issues",
        "Documentation": "https://github.com/G0OZE/EV-Vehicle-charge-demand/docs",
        "Source Code": "https://github.com/G0OZE/EV-Vehicle-charge-demand",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.12.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aicte-workflow=src.cli.workflow_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.txt", "*.md"],
    },
    keywords="aicte, workflow, automation, education, internship, github, jupyter",
    zip_safe=False,
)