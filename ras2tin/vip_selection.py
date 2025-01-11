"""
VIP Selection algorithm. Implementing "Systematic selection of very important points (VIP) from digital terrain model for constructing triangular irregular network", Zhimin Chen, 1987
"""
import numpy as np
import rasterio
from .utils import pad_array, conv2d

def vip_selection(elevation_data, metadata, ratio, n_cells):
    # Ensure n_cells is even
    if n_cells % 2 != 0:
        raise ValueError("n_cells must be an even number.")

    laplacian = np.array([
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1]
    ])

    data = pad_array(elevation_data)  # Add padding
    significance = conv2d(data, laplacian)
    data = data[1:-1, 1:-1]

    tot_points = data.size
    limit = int(0.5 * tot_points * ratio)

    # Divide the limit equally among the cells
    points_per_cell = limit // n_cells

    height, width = data.shape
    # Determine grid dimensions (n_cells total cells)
    grid_rows = int(np.sqrt(n_cells))
    grid_cols = n_cells // grid_rows
    cell_height = height // grid_rows
    cell_width = width // grid_cols

    vip = np.zeros_like(data, dtype=bool)

    for i in range(grid_rows):
        for j in range(grid_cols):
            # Define the bounds of the current cell
            row_start, row_end = i * cell_height, (i + 1) * cell_height
            col_start, col_end = j * cell_width, (j + 1) * cell_width

            # Handle edge cases for last cell rows/columns
            if i == grid_rows - 1:
                row_end = height
            if j == grid_cols - 1:
                col_end = width

            # Extract the cell data and significance values
            cell_data = data[row_start:row_end, col_start:col_end]
            cell_significance = significance[row_start:row_end, col_start:col_end]

            # Flatten the significance array for sorting
            flat_arr = cell_significance.flatten()

            # Select points with the highest and lowest significance
            largest_indices = np.argsort(flat_arr)[-points_per_cell:]
            smallest_indices = np.argsort(flat_arr)[:points_per_cell]

            # Create a boolean mask for the selected points in the cell
            cell_vip = np.zeros_like(cell_data, dtype=bool)
            cell_vip.ravel()[largest_indices] = True
            cell_vip.ravel()[smallest_indices] = True

            # Update the global VIP mask
            vip[row_start:row_end, col_start:col_end] = cell_vip

    # Convert the selected points to a list of coordinates and heights
    height, width = vip.shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(metadata['transform'], rows, cols)
    xcoords = np.array(xs).reshape(vip.shape)
    ycoords = np.array(ys).reshape(vip.shape)

    xindex, yindex = np.where(vip)
    vip_points = []
    for x, y in zip(xindex, yindex):
        vip_points.append([xcoords[x, y], ycoords[x, y], data[x, y]])

    vip_points = np.array(vip_points)
    return vip_points
