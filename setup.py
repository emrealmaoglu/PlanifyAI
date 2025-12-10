from setuptools import setup, find_packages

setup(
    name="planifyai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26.2",
        "scipy>=1.11.4",
        "pandas>=2.1.3",
        "geopandas>=0.14.1",
        "shapely>=2.0.2",
        "pymoo>=0.6.1.1",
    ],
)
