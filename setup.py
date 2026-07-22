from setuptools import setup, find_packages

setup(
    name="crosswire",
    version="2.0.0",
    description="AI-powered content syndication engine — cross-post to 14 platforms",
    author="Yash Brahmankar",
    author_email="yashbrahmankar95@gmail.com",
    url="https://github.com/loisekk/crosswire",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.0",
        "playwright>=1.40.0",
        "flask>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "crosswire=main:main",
            "crosswire-dashboard=dashboard.app:run_dashboard",
            "crosswire-supervisor=supervisor:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
    ],
)
