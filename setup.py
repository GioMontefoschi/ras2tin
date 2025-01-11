from setuptools import setup, find_packages

setup(
    name="ras2tin",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'rasterio',
        'scipy',
        'plotly',
        'fiona',
        'shapely'
    ],
    description="A simple library to convert and display TINs from a DEM",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Giovanni Montefoschi",
    author_email="giovannimontefoschi@gmail.com",
    url="https://github.com/GioMontefoschi/ras2tin.git",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
