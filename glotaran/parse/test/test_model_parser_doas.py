# unused import
# from glotaran.model import FixedConstraint, BoundConstraint
# from os import getcwd
from os.path import abspath
from os.path import dirname
from os.path import join

import pytest

from glotaran.builtin.models.doas import DOASMegacomplex
from glotaran.builtin.models.doas import DOASModel
from glotaran.builtin.models.doas import Oscillation
from glotaran.parse.parser import load_yml_file

THIS_DIR = dirname(abspath(__file__))


@pytest.fixture
def model():
    spec_path = join(THIS_DIR, "test_model_spec_doas.yml")
    return load_yml_file(spec_path)


def test_correct_model(model):
    assert isinstance(model, DOASModel)


def test_oscillation(model):
    assert len(model.oscillation) == 2

    i = 1
    for _ in model.oscillation:
        label = f"osc{i}"
        assert label in model.oscillation
        oscillation = model.oscillation[label]
        assert isinstance(oscillation, Oscillation)
        assert oscillation.label == label
        assert oscillation.frequency == i
        assert oscillation.rate == 2 + i

        i = i + 1


def test_megacomplexes(model):
    assert len(model.megacomplex) == 4

    i = 1
    for _ in model.megacomplex:
        label = f"cmplx{i}"
        assert label in model.megacomplex
        megacomplex = model.megacomplex[label]
        assert isinstance(megacomplex, DOASMegacomplex)
        assert megacomplex.label == label
        assert megacomplex.k_matrix == [f"km{i}"]
        if i == 2:
            assert megacomplex.oscillation == ["osc1"]
        if i == 4:
            assert megacomplex.oscillation == ["osc2"]

        i = i + 1
