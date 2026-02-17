from setuptools import setup, find_packages

setup(
    name="GravityKit",
    version="3.1.0",
    packages=["GravityKit"],
    include_package_data=True,
    install_requires=[
        "requests",
        "beautifulsoup4",
        "click",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "gk=GravityKit.cli:main",
            "gravitykit=GravityKit.cli:main",
        ],
    },
    author="GravityKit Team",
    description="The AI-Native Software House in a Box",
)
