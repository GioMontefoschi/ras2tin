import pytest
import numpy as np
from ras2tin.tin import TIN
from ras2tin.utils import pad_array, conv2d, slope, aspect
from ras2tin.vip_selection import vip_selection

# Fixtures
@pytest.fixture
def mock_raster():
    """Mock raster data for testing."""
    return np.array([
        [100, 102, 104, 106, 108, 110, 112, 114],
        [98, 100, 102, 104, 106, 108, 110, 112],
        [96, 98, 100, 102, 104, 106, 108, 110],
        [94, 96, 98, 100, 102, 104, 106, 108],
        [92, 94, 96, 98, 100, 102, 104, 106],
        [90, 92, 94, 96, 98, 100, 102, 104],
        [88, 90, 92, 94, 96, 98, 100, 102],
        [86, 88, 90, 92, 94, 96, 98, 100]
    ])

@pytest.fixture
def mock_metadata():
    """Mock metadata with transform and CRS."""
    return {
        'transform': rasterio.transform.from_origin(0, 0, 1, 1),
        'crs': 'EPSG:4326'
    }

# Test pad_array
def test_pad_array(mock_raster):
    padded = pad_array(mock_raster)
    assert padded.shape == (10, 10)
    np.testing.assert_array_equal(padded[1:-1, 1:-1], mock_raster)

# Test conv2d
def test_conv2d(mock_raster):
    kernel = np.array([
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1]
    ])
    result = conv2d(pad_array(mock_raster), kernel)
    assert result.shape == mock_raster.shape

# Test slope and aspect
def test_slope_aspect():
    points = np.array([
        [0, 0, 100],
        [1, 0, 105],
        [0, 1, 95]
    ])
    triangles = np.array([[0, 1, 2]])
    assert np.isclose(slope(points, triangles)[0], 45, atol=5)
    assert 0 <= aspect(points, triangles)[0] < 360

# Test vip_selection
def test_vip_selection(mock_raster, mock_metadata):
    ratio = 0.1
    n_cells = 4
    vip_points = vip_selection(mock_raster, mock_metadata, ratio, n_cells)
    assert vip_points.shape[1] == 3  # Each point should have x, y, z

# Test TIN class
def test_tin_class(tmp_path, mock_raster, mock_metadata):
    # Mock raster file
    raster_file = tmp_path / "mock_raster.tif"
    with rasterio.open(
        raster_file, 'w', driver='GTiff',
        height=mock_raster.shape[0],
        width=mock_raster.shape[1],
        count=1, dtype=mock_raster.dtype,
        crs=mock_metadata['crs'],
        transform=mock_metadata['transform']
    ) as dst:
        dst.write(mock_raster, 1)

    tin = TIN(raster_file)
    tin.generate_points(ratio=0.1, n_cells=4)
    tin.generate_tin()

    assert tin.points is not None
    assert tin.triangles is not None

    error_map = tin.error_map()
    assert error_map.shape == mock_raster.shape

    fig = tin.plot()
    assert fig is not None

    tin.get_slope()
    tin.get_aspect()
    assert tin.slope is not None
    assert tin.aspect is not None

    output_file = tmp_path / "tin_output.gpkg"
    tin.to_file(output_file)
    assert output_file.exists()
