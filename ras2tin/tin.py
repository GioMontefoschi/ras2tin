'''
Raster 2 Triangulated Irregular Network
by Giovanni Montefoschi
'''
import numpy as np
import rasterio
from scipy.spatial import Delaunay
import vip_selection
import plotly.graph_objects as go

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

    def plot(self, **kwargs):
        '''
        Convenience function to plot using the plotly library
        '''
        if self.triangles is None:
            self.triangles = self.generate_tin()
        # Extract x, y, z coordinates from the points
        x, y, z = self.points[:, 0], self.points[:, 1], self.points[:, 2]
        # Extract i, j, k indices from the triangles
        i, j, k = self.triangles[:, 0], self.triangles[:, 1], self.triangles[:, 2]
        # Create the Mesh3d plot for the tin
        colorscale=[
                [0.0, 'rgb(0, 0, 128)'],   # Deep blue for lowest elevation
                [0.2, 'rgb(0, 128, 255)'], # Light blue for water-like elevation
                [0.4, 'rgb(0, 255, 0)'],   # Green for lowlands
                [0.6, 'rgb(255, 255, 0)'], # Yellow for mid-elevation
                [0.8, 'rgb(255, 165, 0)'], # Orange for highlands
                [1.0, 'rgb(255, 0, 0)']    # Red for peaks
            ]
        opacity = 0.8
        colorbar = dict(title='Elevation [m]')
        if 'colorscale' in kwargs:
            colorscale = kwargs['colorscale']
        if 'opacity' in kwargs:
            opacity = kwargs['opacity']
        if 'colorbar' in kwargs:
            colorbar = kwargs['colorbar']


        mesh = go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            opacity=opacity,
            intensity=z,  # Use z values for intensity
            colorscale=colorscale,
            colorbar=colorbar
        )

        # Create the figure with specified dimensions
        if 'height' in kwargs and 'width' in kwargs:
            height = kwargs['height']
            width = kwargs['width']
        else:
            height = 800
            widt = 1000
        fig = go.Figure(data=[mesh], layout=go.Layout(height=height, width=height))

        #Update the layout for better visualization
        if 'title' in kwargs:
            title = kwargs['title']
        else:
            title = '3D Mesh Visualization with Terrain Elevation'

        fig.update_layout(
            scene=dict(
                xaxis_title='X Axis',
                yaxis_title='Y Axis',
                zaxis_title='Z Axis',
                aspectmode='data'  # Ensures all axes are scaled equally
            ),
            title=title
        )

        return fig
