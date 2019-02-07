import typing
import numpy as np
import xarray as xr


def prepare_dataset(dataset: typing.Union[xr.DataArray, xr.Dataset],
                    weight: np.ndarray = None) -> xr.Dataset:

    if isinstance(dataset, xr.DataArray):
        dataset = dataset.to_dataset(name="data")

    if'data_singular_values' not in dataset:
        l, s, r = np.linalg.svd(dataset.data)
        dataset['data_left_singular_vectors'] = \
            (('time', 'left_singular_value_index'), l)
        dataset['data_singular_values'] = (('singular_value_index'), s)
        dataset['data_right_singular_vectors'] = \
            (('right_singular_value_index', 'spectral'), r)

    if weight:
        dataset['weight'] = (dataset.data.dims, weight)
        dataset['weighted_data'] = (dataset.data.dims,
                                    np.multiply(dataset.data, dataset.weight))

    return dataset
