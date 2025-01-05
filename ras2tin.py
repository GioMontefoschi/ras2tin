'''
Raster 2 Triangulated Irregular Network
by Giovanni Montefoschi
'''
import numpy as np
import rasterio

laplacian = np.array([
    [-1, -1, -1],
    [-1, 8, -1],
    [-1, -1, -1]
])


def pad_array(arr):
    """
    Pads a given n x m numpy array with mirrored values around the borders.
    Corners are handled by averaging the adjacent values.

    Parameters:
    arr (numpy.ndarray): Input 2D array of shape (n, m).

    Returns:
    numpy.ndarray: Padded array of shape (n+2, m+2).
    """
    # Validate input
    if arr.ndim != 2:
        raise ValueError("Input array must be 2-dimensional.")

    # Original dimensions
    n, m = arr.shape

    # Initialize padded array
    padded = np.zeros((n + 2, m + 2), dtype=arr.dtype)

    # Fill the central area with the original array
    padded[1:n+1, 1:m+1] = arr

    # Fill the top and bottom rows
    padded[0, 1:m+1] = arr[0, :]  # Top row
    padded[n+1, 1:m+1] = arr[-1, :]  # Bottom row

    # Fill the left and right columns
    padded[1:n+1, 0] = arr[:, 0]  # Left column
    padded[1:n+1, m+1] = arr[:, -1]  # Right column

    # Handle corners with averages
    padded[0, 0] = (arr[0, 0] + arr[0, 1] + arr[1, 0]) / 3  # Top-left corner
    padded[0, m+1] = (arr[0, -1] + arr[0, -2] + arr[1, -1]) / 3  # Top-right corner
    padded[n+1, 0] = (arr[-1, 0] + arr[-1, 1] + arr[-2, 0]) / 3  # Bottom-left corner
    padded[n+1, m+1] = (arr[-1, -1] + arr[-1, -2] + arr[-2, -1]) / 3  # Bottom-right corner

    return padded

def conv2d(array, kernel):
    '''
    This function is used to apply the 2d convolution
    '''
    # Get the dimensions of the input array
    rows, cols = array.shape

    # Extract all overlapping 3x3 patches as a 3D array
    patches = np.lib.stride_tricks.sliding_window_view(array, (3, 3))

    # Perform element-wise multiplication and sum over the last two axes
    output = np.tensordot(patches, kernel, axes=([2, 3], [0, 1]))

    return output


def vip_selection(dem, ratio=0.1):
    '''
        This function is used to select very important points from the raster containing the dem
        Parameters:
            dem: path to the raster to be converted
            kernel_size: the size (nxn) of the Sobel filters to be used
            n_points: the number of points to extract for creating the TIN
        Returns:
            points: np.ndarray of shape 3xn_points with the extracted points
    '''

    try:
        with rasterio.open(dem) as raster:
            data = raster.read(1) #Read the first band of the raster
            metadata = raster.meta #Read the metadata
    except FileNotFoundError:
        print(f"Error: The file at path '{dem}' could not be found.")
        return None, None
    except Exception as e:
        print(f"Error: Failed to open raster file '{dem}'. Details: {e}")

    data = pad_array(data) #Add padding
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
    #Set the four corners to be always used, this is convenient to tile multiple rasters together
    vip[0,0] = True #Top left
    vip[0, -1] = True #Top right
    vip[-1, 0] = True #Bottom left
    vip[-1, -1] = True #Bottom right
    #Now just convert these points to a list of coordinates and heights
    height, width = vip.shape #Find the height and width of the array
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(metadata['transform'], rows, cols)
    xcoords = np.array(xs)
    ycoords = np.array(ys)

    xindex, yindex = np.where(vip==True) #Find index of all true values in vip
    vip_points = []
    for x, y in zip(xindex, yindex):
        vip_points.append([xcoords[x], ycoords[y], data[x, y]])
    vip_points = np.array(vip_points)

    return vip_points

