import numpy as np
import pytest
import xarray as xr

from glotaran.analysis.scheme import Scheme
from glotaran.parameter import ParameterGroup

from .mock import MockModel


@pytest.fixture(scope="session")
def scheme(tmpdir_factory):

    path = tmpdir_factory.mktemp("scheme")

    model = "type: mock\ndataset:\n  dataset1:\n    megacomplex: []"
    model_path = path.join("model.yml")
    with open(model_path, "w") as f:
        f.write(model)

    parameter = "[1.0, 67.0]"
    parameter_path = path.join("parameter.yml")
    with open(parameter_path, "w") as f:
        f.write(parameter)

    dataset_path = path.join("dataset.nc")
    xr.DataArray([1, 2, 3]).to_dataset(name="data").to_netcdf(dataset_path)

    extra_path = path.join("extradata.nc")
    xr.DataArray([1, 2, 3]).to_netcdf(extra_path)

    scheme = f"""
    model: {model_path}
    parameter: {parameter_path}
    nnls: True
    nfev: 42
    data:
      dataset1: {dataset_path}
    extra:
        testextra: {extra_path}
    """
    scheme_path = path.join("scheme.gta")
    with open(scheme_path, "w") as f:
        f.write(scheme)
    return scheme_path


def test_scheme(scheme):
    scheme = Scheme.from_yml_file(scheme)
    assert scheme.model is not None
    assert scheme.model.model_type == "mock"

    assert scheme.parameter is not None
    assert scheme.parameter.get("1") == 1.0
    assert scheme.parameter.get("2") == 67.0

    assert scheme.nnls
    assert scheme.nfev == 42

    assert "dataset1" in scheme.data
    assert isinstance(scheme.data["dataset1"], xr.DataArray)
    assert scheme.data["dataset1"].data.size == 3

    assert "testextra" in scheme.extra
    assert isinstance(scheme.extra["testextra"], xr.DataArray)
    assert scheme.extra["testextra"].size == 3


def test_weight():
    model_dict = {
        "dataset": {
            "dataset1": {
                "megacomplex": [],
            },
        },
        "weights": [
            {
                "datasets": ["dataset1"],
                "global_interval": (np.inf, 200),
                "model_interval": (4, 8),
                "value": 0.5,
            },
        ],
    }
    model = MockModel.from_dict(model_dict)
    print(model.validate())
    assert model.valid()

    parameter = ParameterGroup.from_list([])

    global_axis = np.asarray(range(50, 300))
    model_axis = np.asarray(range(15))

    dataset = xr.DataArray(
        np.ones((global_axis.size, model_axis.size)),
        coords={"e": global_axis, "c": model_axis},
        dims=("e", "c"),
    )

    scheme = Scheme(model, parameter, {"dataset1": dataset})

    data = scheme.prepare_data()["dataset1"]
    print(data)
    assert "data" in data
    assert "weight" in data

    assert data.data.shape == data.weight.shape
    assert np.all(data.weight.sel(e=slice(0, 200), c=slice(4, 8)).values == 0.5)
    assert np.all(data.weight.sel(c=slice(0, 3)).values == 1)

    model_dict["weights"].append(
        {
            "datasets": ["dataset1"],
            "value": 0.2,
        }
    )
    model = MockModel.from_dict(model_dict)
    print(model.validate())
    assert model.valid()

    scheme = Scheme(model, parameter, {"dataset1": dataset})
    data = scheme.prepare_data()["dataset1"]
    assert np.all(data.weight.sel(e=slice(0, 200), c=slice(4, 8)).values == 0.5 * 0.2)
    assert np.all(data.weight.sel(c=slice(0, 3)).values == 0.2)

    scheme = Scheme(model, parameter, {"dataset1": data})
    pytest.warns(UserWarning, scheme.prepare_data)
