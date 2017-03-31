from collections import OrderedDict
import numpy as np

from .matrix_group import MatrixGroup


class MatrixGroupGenerator(object):
    def __init__(self):
        self._groups = OrderedDict()

    @classmethod
    def for_model(cls, model, xtol=0.5):
        gen = cls()
        gen._init_groups_for_model(model, xtol)
        return gen

    @classmethod
    def for_dataset(cls, model, dataset):
        gen = cls()
        data = model.datasets[dataset]
        gen._add_dataset_to_group(model, data, 0)
        return gen

    def _init_groups_for_model(self, model, xtol):
        for _, dataset in model.datasets.items():
            self._add_dataset_to_group(model, dataset, xtol)

    def _add_dataset_to_group(self, model, dataset, xtol):
            for matrix in [model.calculated_matrix()(x, dataset, model) for x
                           in dataset.data.get_estimated_axis()]:
                self._add_c_matrix_to_group(matrix, xtol)

    def _add_c_matrix_to_group(self, matrix, xtol):
                if matrix.x in self._groups:
                    self._groups[matrix.x].add_cmatrix(matrix)
                elif any(abs(matrix.x-val) < xtol for val in self._groups):
                    idx = [val for val in self._groups if abs(matrix.x-val) <
                           xtol][0]
                    self._groups[idx].add_cmatrix(matrix)
                else:
                    self._groups[matrix.x] = MatrixGroup(matrix)

    def groups(self):
        for _, group in self._groups.items():
            yield group

    def calculate(self, parameter):
        return [group.calculate(parameter) for group in self.groups()]

    def create_dataset_group(self):

        dataset_group = []
        for _, group in self._groups.items():
            slices = []
            for mat in group.c_matrices:
                x = np.where(mat.dataset.data.get_estimated_axis ==
                             mat.x)[0]
                slices.append(mat.dataset.data.data[:, x])
            slice = np.append([], slices)
            dataset_group.append(slice)

        return dataset_group