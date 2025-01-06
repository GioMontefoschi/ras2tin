"""
Utility functions I made here and there
"""
import numpy as np

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
