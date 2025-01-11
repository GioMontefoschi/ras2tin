'''
Raster 2 Triangulated Irregular Network
by Giovanni Montefoschi
'''
import numpy as np
import rasterio
import fiona
from fiona.crs import from_epsg
from shapely.geometry import Polygon
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
from .vip_selection import vip_selection
from .utils import aspect, slope
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
        self.slope = None
        self.aspect = None
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

    def generate_points(self, ratio=0.04, n_cells=64):
        """
        Select a set of important points (VIPs) from the elevation data.

        Returns:
        numpy.ndarray: Array of points with shape (n, 3).
        """
        if self.elevation_data is None:
            raise ValueError("Elevation data not loaded.")
        self.points = vip_selection(elevation_data=self.elevation_data, metadata=self.metadata, ratio=ratio, n_cells=n_cells)

    def generate_tin(self):
        """
        Generate a TIN using scipy's Delaunay class for convenience
        """
        if self.points is None:
            self.points = self.generate_points()
        delaunay_tri = Delaunay(self.points[:, :2])
        self.triangles = delaunay_tri.simplices

    def error_map(self):
        """
        A function to assess the error of the TIN wrt the original raster data
        """
        # Set up the interpolator
        interpolator = LinearNDInterpolator(Delaunay(self.points[:, :2]), self.points[:, -1])
        # Convert the selected points to a list of coordinates and heights
        height, width = self.elevation_data.shape
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        xcoords, ycoords = rasterio.transform.xy(self.metadata['transform'], rows, cols)
        Z = interpolator(xcoords, ycoords)
        Z_interpolated = np.array(Z).reshape(self.elevation_data.shape)
        error = Z_interpolated - self.elevation_data

        return error

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

    def get_slope(self):
        if self.triangles is None:
            print('No triangles have been generated yet!')
            return None
        if self.points is None:
            print('No points have been generated yet!')
            return None
        self.slope = slope(self.points, self.triangles)
        return self.slope

    def get_aspect(self):
        if self.triangles is None:
            print('No triangles have been generated yet!')
            return None
        if self.points is None:
            print('No points have been generated yet!')
            return None
        self.aspect = aspect(self.points, self.triangles)
        return self.aspect

    def to_file(self, filepath, driver='GPKG'):
        """
        Writes the TIN triangles to a shapefile or GeoPackage with slope and aspect as attributes if present.

        Parameters:
        - filepath: str, path to the output file.
        - driver: str, output file format driver (e.g., "GPKG" or "ESRI Shapefile").
        """

        props = {}

        if self.slope is not None:
            props['slope'] = 'float'
        if self.aspect is not None:
            props['aspect'] = 'float'

        schema = {
            'geometry': 'Polygon',
            'properties': props
        }

        crs_string = self.metadata["crs"].to_string()
        epsg_code = int(crs_string.split(":")[1])  # Extract the EPSG code from the CRS string
        crs = from_epsg(epsg_code)

        with fiona.open(filepath, mode='w', driver=driver, crs=crs, schema=schema) as layer:
            for i, triangle in enumerate(self.triangles):
                vertices = self.points[triangle]
                polygon = Polygon(vertices[:, :2])
                if not polygon.is_valid:
                    continue  # Skip invalid polygons

                properties = {}
                if self.slope is not None:
                    properties['slope'] = float(self.slope[i])
                if self.aspect is not None:
                    properties['aspect'] = float(self.aspect[i])

                # Write geometry and properties if they exist
                layer.write({
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [list(polygon.exterior.coords)]
                    },
                    'properties': properties
                })
