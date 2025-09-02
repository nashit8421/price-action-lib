from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="price-action-lib",
    version="1.0.0",
    author="Your Name",  # Replace with your actual name
    author_email="your.email@example.com",  # Replace with your email
    description="A comprehensive price action analysis library for Indian stock market",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/price-action-lib",  # Replace with your GitHub repo
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="price action, trading, stock market, candlestick patterns, technical analysis, indian stocks, NSE, BSE",
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    project_urls={
        "Documentation": "https://github.com/yourusername/price-action-lib#readme",
        "Bug Reports": "https://github.com/yourusername/price-action-lib/issues",
        "Source": "https://github.com/yourusername/price-action-lib",
    },
)