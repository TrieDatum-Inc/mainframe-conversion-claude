from setuptools import find_packages, setup

setup(
    name="carddemo_batch",
    version="1.0.0",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "pyspark>=3.3.0",
        "delta-spark>=2.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-spark>=0.6",
            "chispa>=0.9",
        ],
    },
)
