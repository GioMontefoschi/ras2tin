from setuptools import setup, find_packages

setup(
    name="ras2tin",  # Name of your package
    version="0.1",  # Version number
    packages=find_packages(where="ras2tin"),  # This will include the ras2tin directory and its submodules
    package_dir={"": "ras2tin"},  # Specifies that the package is inside the ras2tin directory
    install_requires=[
        # List any dependencies your library needs here (e.g., 'numpy', 'requests')
    ],
)
