from setuptools import setup, find_packages

setup(
    name="football_tactical_analyzer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python library for football tactical analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/football-tactical-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Sports Professionals",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
        "networkx>=2.5",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
        "viz": [
            "plotly>=5.0.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
        ],
        "web": [
            "streamlit>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "football-analyze=analyzer.cli:main",
        ],
    },
)