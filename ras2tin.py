'''
Raster 2 Triangulated Irregular Network
by Giovanni Montefoschi
'''
import numpy as np
import rasterio
from scipy.spatial import Delaunay
import vip_selection

class TIN:
    """
    A class to represent a Triangulated Irregular Network (TIN) generated from a raster file.
    """

    def __init__(self, raster_path):
        """
        Initialize the TIN object by loading a raster file.

        Parameters:
        raster_path (str): Path to the raster file (e.g., DEM).
        """
        self.raster_path = raster_path
        self.elevation_data = None
        self.points = None
        self.triangles = None
        self.edges = None
        self.load_raster()

    def load_raster(self):
        """
        Load elevation data from the raster file into a numpy array.
        """
        try:
            with rasterio.open(self.raster_path) as dataset:
                self.elevation_data = dataset.read(1)
                self.metadata = dataset.meta  # Save geotransform for spatial referencing
        except Exception as e:
            print(f"Error loading raster: {e}")

    def generate_points(self, ratio=0.1):
        """
        Select a set of important points (VIPs) from the elevation data.

        Returns:
        numpy.ndarray: Array of points with shape (n, 3).
        """
        if self.elevation_data is None:
            raise ValueError("Elevation data not loaded.")
        self.points = vip_selection.vip_selection(elevation_data=self.elevation_data, metadata=self.metadata, ratio=ratio)

    def generate_tin(self):
        """
        Generate a TIN using scipy's Delaunay class for convenience
        """
        if self.points is None:
            self.points = self.generate_points()
        delaunay_tri = Delaunay(self.points[:, :2])
        self.triangles = delaunay_tri.simplices

    def get_triangles(self):
        """
        Return list of triangles of the TIN
        """
        if self.triangles is None:
            self.triangles = self.generate_tin()
        return self.triangles

    def get_points(self):
        """
        Return list of points in the tin (vertex)
        """
        if self.points is None:
            self.points = self.generate_points()
        return self.points
