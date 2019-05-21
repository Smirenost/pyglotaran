import collections
import dask
import dask.bag as db
import numpy as np

from glotaran.parameter import ParameterGroup

LabelAndMatrix = collections.namedtuple('LabelAndMatrix', 'clp_label matrix')
LabelAndMatrixAndData = collections.namedtuple('LabelAndMatrixAndData', 'label_matrix data')


def create_index_independend_ungrouped_matrix_jobs(scheme, parameter_client):

    clp_label = {}
    matrix_jobs = {}
    constraint_matrix_jobs = {}
    model = scheme.model

    parameter = _get_parameter(parameter_client)
    for label, descriptor in scheme.model.dataset.items():
        descriptor = dask.delayed(descriptor.fill)(model, parameter)
        clp, matrix = dask.delayed(_calculate_matrix, nout=2)(
            model.matrix,
            descriptor,
            scheme.data[label].coords[model.matrix_dimension].values,
            {},
        )
        clp_label[label] = clp
        matrix_jobs[label] = matrix
        if callable(model.constrain_matrix_function):
            clp, matrix = model.constrain_matrix_function(parameter, clp, matrix, None)
        constraint_matrix_jobs[label] = (clp, matrix)
    return clp_label, matrix_jobs, constraint_matrix_jobs


def create_index_independend_grouped_matrix_jobs(scheme, groups, parameter_client):

    model = scheme.model

    descriptors = {label: _fill_dataset_descriptor(model, descriptor, parameter_client)
                   for label, descriptor in model.dataset.items()}
    parameter_future = _get_parameter(parameter_client)

    @dask.delayed
    def calculate_matrices():
        parameter = parameter_future.compute()
        matrices = {}

        ds = dask.compute(descriptors)[0]
        for label, descriptor in model.dataset.items():
            descriptor = descriptor.fill(model, parameter)
            matrices[label] = _calculate_matrix(
                model.matrix,
                ds[label],
                scheme.data[label].coords[model.matrix_dimension].values,
                {},
            )

        for label, group in groups.items():
            if label not in matrices:
                matrices[label] = _combine_matrices(
                            [matrices[d] for d in group]
                        )
        return matrices

    @dask.delayed
    def retrieve_clp(matrices):
        return {label: matrices[label][0] for label in model.dataset}

    @dask.delayed
    def retrieve_matrices(matrices):
        return {label: matrices[label][1] for label in model.dataset}

    @dask.delayed
    def constrain_matrices(matrices):
        constraint = {}
        if callable(model.constrain_matrix_function):
            parameter = parameter_future.compute()
            for label in matrices:
                clp, matrix = matrices[label]
                constraint[label] = model.constrain_matrix_function(parameter, clp, matrix, None)
        else:
            constraint = matrices
        return constraint

    matrices = calculate_matrices()
    return retrieve_clp(matrices), retrieve_matrices(matrices), constrain_matrices(matrices)


def create_index_dependend_ungrouped_matrix_jobs(scheme, bag, parameter_client):

    model = scheme.model
    clps = {}
    matrix_jobs = {}
    constraint_matrix_jobs = {}

    parameter = _get_parameter(parameter_client)
    for label, problem in bag.items():
        descriptor = dask.delayed(model.dataset[label].fill)(model, parameter)
        clps[label] = []
        matrix_jobs[label] = []
        constraint_matrix_jobs[label] = []
        for index in problem.global_axis:
            clp, matrix = dask.delayed(_calculate_matrix, nout=2)(
                model.matrix,
                descriptor,
                problem.matrix_axis,
                {},
                index=index,
            )
            clps[label].append(clp)
            matrix_jobs[label].append(matrix)
            if callable(model.constrain_matrix_function):
                clp, matrix = model.constrain_matrix_function(parameter, clp, matrix, index)
            constraint_matrix_jobs[label].append((clp, matrix))

    return clps, matrix_jobs, constraint_matrix_jobs


def create_index_dependend_grouped_matrix_jobs(scheme, bag, parameter_client):

    model = scheme.model

    descriptors = {label: _fill_dataset_descriptor(model, descriptor, parameter_client)
                   for label, descriptor in model.dataset.items()}

    parameter = _get_parameter(parameter_client)

    def calculate_group(group):
        ds = dask.compute(descriptors)[0]
        results = [_calculate_matrix(
            model.matrix,
            ds[problem.dataset],
            problem.axis,
            {},
            index=problem.index
        ) for problem in group.descriptor]
        return results, group.descriptor[0].index

    def get_clp(result):
        return [d[0] for d in result[0]]

    def get_matrices(result):
        return [d[1] for d in result[0]]

    def constrain_and_combine_matrices(result):
        matrices, index = result
        clp, matrix = _combine_matrices(matrices)
        if callable(model.constrain_matrix_function):
            clp, matrix = model.constrain_matrix_function(parameter, clp, matrix, index)
        return clp, matrix

    matrix_jobs = bag.map(calculate_group)
    constraint_matrix_jobs = matrix_jobs.map(constrain_and_combine_matrices)
    clp = matrix_jobs.map(get_clp)
    matrices = matrix_jobs.map(get_matrices)
    return clp, matrices, constraint_matrix_jobs


@dask.delayed
def _get_parameter(parameter_client):
    parameter = parameter_client.get().result()
    parameter = ParameterGroup.from_parameter_dict(parameter)
    return parameter


@dask.delayed
def _fill_dataset_descriptor(model, descriptor, parameter_client):
    return _fill_dataset_descriptor_non_delayed(model, descriptor, parameter_client)


def _fill_dataset_descriptor_non_delayed(model, descriptor, parameter_client):
    parameter = parameter_client.get().result()
    parameter = ParameterGroup.from_parameter_dict(parameter)
    return descriptor.fill(model, parameter)


def _calculate_matrix(matrix_function, dataset_descriptor, axis, extra, index=None):
    args = {
        'dataset_descriptor': dataset_descriptor,
        'axis': axis,
    }
    for k, v in extra:
        args[k] = v
    if index is not None:
        args['index'] = index
    clp_label, matrix = matrix_function(**args)
    if dataset_descriptor.scale is not None:
        matrix *= dataset_descriptor.scale
    return clp_label, matrix


def _combine_matrices(label_and_matrices):
    (all_clp, matrices) = ([], [])
    masks = []
    full_clp = None
    for label_and_matrix in label_and_matrices:
        (clp, matrix) = label_and_matrix
        matrices.append(matrix)
        if full_clp is None:
            full_clp = clp
            masks.append([i for i, _ in enumerate(clp)])
        else:
            mask = []
            for c in clp:
                if c not in full_clp:
                    full_clp.append(c)
                mask.append(full_clp.index(c))
            masks.append(mask)
    dim1 = np.sum([m.shape[0] for m in matrices])
    dim2 = len(full_clp)
    matrix = np.zeros((dim1, dim2), dtype=np.float64)
    start = 0
    for i, m in enumerate(matrices):
        end = start + m.shape[0]
        matrix[start:end, masks[i]] = m
        start = end

    return (full_clp, matrix)