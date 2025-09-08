"""Setup script for STARLOG MCP."""

from setuptools import setup, find_packages

setup(
    name="starlog-mcp",
    version="0.1.0",
    description="STARLOG documentation workflow MCP for Claude Code",
    packages=find_packages(),
    install_requires=[
        "fastmcp",
        "pydantic>=2.0.0",
        # Note: heaven-base should be available in the environment
        # "heaven-base>=0.1.0",  # Uncomment when available
    ],
    entry_points={
        "console_scripts": [
            "starlog-server=starlog_mcp.starlog_mcp:main",
        ],
    },
    python_requires=">=3.8",
    author="Isaac and Claude",
    author_email="noreply@anthropic.com",
    url="https://github.com/anthropics/claude-code",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)