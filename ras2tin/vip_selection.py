"""
VIP Selection algorithm. Implementing "Systematic selection of very important points (VIP) from digital terrain model for constructing triangular irregular network", Zhimin Chen, 1987
"""
import numpy as np
import rasterio
from .utils import pad_array, conv2d

laplacian = np.array([
    [-1, -1, -1],
    [-1, 8, -1],
    [-1, -1, -1]
])

def vip_selection(elevation_data, metadata, ratio):
    data = pad_array(elevation_data) #Add padding
    significance = conv2d(data, laplacian)
    data = data[1:-1, 1:-1]

    tot_points = data.size
    #Limit is the number of points to keep in order to construct the tin
    limit = int(0.5*tot_points*ratio)
    #First get index of the tails of the histogram
    flat_arr = significance.flatten()
    largest_indices = np.argsort(flat_arr)[-limit:]
    smallest_indices = np.argsort(flat_arr)[:limit]
    #Then create a boolean mask of the selected points
    vip = np.zeros_like(data, dtype=bool)
    vip.ravel()[largest_indices] = True
    vip.ravel()[smallest_indices] = True
    #Now just convert these points to a list of coordinates and heights
    height, width = vip.shape #Find the height and width of the array
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(metadata['transform'], rows, cols)
    xcoords = np.array(xs)
    xcoords = xcoords.reshape(vip.shape)
    ycoords = np.array(ys)
    ycoords = ycoords.reshape(vip.shape)

    xindex, yindex = np.where(vip==True) #Find index of all true values in vip
    vip_points = []
    for x, y in zip(xindex, yindex):
        vip_points.append([xcoords[x, y], ycoords[x, y], data[x, y]])
    vip_points = np.array(vip_points)
    #print(vip_points)
    return vip_points

