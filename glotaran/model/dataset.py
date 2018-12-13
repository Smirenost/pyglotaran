"""Glotaran Dataset"""

from copy import copy
from typing import Tuple, Union

import numpy as np


class DimensionalityError(Exception):
    """
    Custom exception if data have the wrong dimensionality
    """
    pass


class Dataset:
    """Dataset is a small interface which dataset/-file implementations can
    fullfill in order to be consumable for glotaran.

    The Datasetclass is contains a very simple implementation used for
    simulatind data.
    """

    def __init__(self):
        self._axis = {}
        self._data = None
        self._weight = None

    def get_axis(self, axis_label: str) -> np.ndarray:
        """get_axis gets an axis by its axis_label.

        Parameters
        ----------
        axis_label : str
            The label of the axis.

        Returns
        -------
        axis : np.ndarray
        """
        return self._axis[axis_label]

    def set_axis(self, axis_label: str, axis:  Union[list, tuple, np.ndarray]):
        """

        Parameters
        ----------
        axis_label: str
            label of the axis

        axis: list or np.ndarray
        """
        if not isinstance(axis, (list, tuple, np.ndarray)):
            raise TypeError(f"Axis must be list, tuple or ndarray, got {type(axis)} instead.")
        if any(not _hashable(v) for v in axis):
            raise ValueError("Axis elements must be hashable.")
        if isinstance(axis, (list, tuple)):
            axis = np.asarray(axis)
        self._axis[axis_label] = axis

    def data(self, weighted=False) -> np.ndarray:
        """
        Data of the dataset as np.ndarray of shape (M,N).
        This corresponds to a measurement with M indices (i.e. wavelength, pixel)
        and N time steps.

        Returns
        -------
        data: np.ndarray
            Data of the dataset as np.ndarray of shape (M,N)
        """
        if weighted and self._weight is not None:
            return np.multiply(self._data, self._weight)
        return self._data

    def set_data(self, data: np.ndarray):
        """
        Data of the dataset as np.ndarray of shape (M,N).
        This corresponds to a measurement with M indices (i.e. wavelength, pixel)
        and N time steps.

        Parameters
        ----------
        data: np.ndarray
            Data of the dataset as np.ndarray of shape (M,N)

        """
        if not isinstance(data, np.ndarray):
            raise TypeError("The data needs to be a ndarray")
        if len(data.shape) is not 2:
            raise DimensionalityError("The data needs to be 2-dimensional")
        self._data = data

    def has_weight(self) -> bool:
        """
        Returns wether the dataset contains a weight matrix.

        Returns
        -------
        has_weight : bool
        """
        return self._weight is not None

    def get_weight(self) -> np.ndarray:
        """
        Returns the weight matrix of the daraset.

        Returns
        -------
        weight : np.ndarray
        """
        return self._weight

    def set_weight(self, weight: np.ndarray):
        if not weight.shape == self._data.shape:
            raise Exception(f"Dimension of weight matrix '{weight.shape}' do not match "
                            f"shape of data '{self._data.shape}'")
        self._weight = weight

    def copy(self) -> 'Dataset':
        """
        Returns a copy of the Dataset Object

        Returns
        -------
        dataset : Dataset
        """
        return copy(self)

    def svd(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns the singular value decomposition of a dataset.

        Parameters
        ----------
        dataset : glotaran.model.dataset.Dataset

        Returns
        -------
        tuple :
            (lsv, svals, rsv)

            lsv : np.ndarray
                left singular values
            svals : np.ndarray
                singular values
            rsv : np.ndarray
                right singular values

        """
        lsv, svals, rsv = np.linalg.svd(self.data())
        return lsv, svals, rsv.T


def _hashable(value):
    try:
        # pylint: disable=pointless-statement
        {value: None}
        return True
    except Exception:
        return False
