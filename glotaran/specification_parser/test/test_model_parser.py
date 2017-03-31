from unittest import TestCase
from glotaran.specification_parser import parse_file
from glotaran.models.spectral_temporal import (KineticModel,
                                               GaussianIrf,
                                               SpectralShapeGaussian,
                                               KineticMegacomplex)
from glotaran.model import (InitialConcentration,
                            ZeroConstraint,
                            EqualConstraint,
                            EqualAreaConstraint,
                            Relation,
                            Parameter,
                            FixedConstraint,
                            BoundConstraint
                            )
from os import getcwd
from os.path import join, dirname, abspath
import numpy as np

THIS_DIR = dirname(abspath(__file__))


class TestParser(TestCase):

    def setUp(self):
        print(getcwd())
        spec_path = join(THIS_DIR, 'test_model_spec.yml')
        self.model = parse_file(spec_path)

    def test_compartments(self):
        self.assertTrue(isinstance(self.model.compartments, list))
        self.assertEqual(self.model.compartments, ['s1', 's2', 's3', 's4'])

    def test_model_type(self):
        self.assertTrue(isinstance(self.model, KineticModel))

    def test_dataset(self):
        self.assertTrue(len(self.model.datasets) is 2)

        i = 1
        for _ in self.model.datasets:
            label = "dataset{}".format(i)
            self.assertTrue(label in self.model.datasets)
            dataset = self.model.datasets[label]
            self.assertTrue(dataset.label == label)
            self.assertTrue(dataset.megacomplexes ==
                            ["cmplx{}".format(i)])
            self.assertTrue(dataset.initial_concentration ==
                            "inputD{}".format(i))
            self.assertTrue(dataset.irf == "irf{}".format(i))
            self.assertEqual(dataset.scaling, i)

            self.assertEqual(len(dataset.megacomplex_scaling), 2)

            self.assertTrue('cmplx1' in dataset.megacomplex_scaling)
            self.assertTrue('cmplx2' in dataset.megacomplex_scaling)
            for _, param in dataset.megacomplex_scaling.items():
                self.assertEqual(param, [1, 2])

            self.assertEqual(len(dataset.compartment_scaling), 2)

            self.assertTrue('s1' in dataset.compartment_scaling)
            self.assertTrue('s2' in dataset.compartment_scaling)
            for _, param in dataset.compartment_scaling.items():
                self.assertEqual(param, [3, 4])

            if i is 1:
                self.assertEqual(len(dataset.shapes), 2)
                self.assertTrue("s1" in dataset.shapes)
                self.assertEqual(dataset.shapes["s1"], "shape1")
                self.assertTrue("s2" in dataset.shapes)
                self.assertEqual(dataset.shapes["s2"], "shape2")

            i = i + 1

    def test_initial_concentration(self):
        self.assertTrue(len(self.model.initial_concentrations) is 2)

        i = 1
        for _ in self.model.initial_concentrations:
            label = "inputD{}".format(i)
            self.assertTrue(label in self.model.initial_concentrations)
            initial_concentration = self.model.initial_concentrations[label]
            self.assertTrue(isinstance(initial_concentration,
                                       InitialConcentration))
            self.assertTrue(initial_concentration.label == label)
            self.assertTrue(initial_concentration.parameter == [1, 2, 3])

    def test_irf(self):
        self.assertTrue(len(self.model.irfs) is 2)

        i = 1
        for _ in self.model.irfs:
            label = "irf{}".format(i)
            self.assertTrue(label in self.model.irfs)
            irf = self.model.irfs[label]
            self.assertTrue(isinstance(irf, GaussianIrf))
            self.assertTrue(irf.label == label)
            want = [1] if i is 1 else [1, 2]
            self.assertEqual(irf.center, want)
            want = [2] if i is 1 else [3, 4]
            self.assertEqual(irf.width, want)
            want = [3] if i is 1 else [5, 6]
            self.assertEqual(irf.center_dispersion, want)
            want = [4] if i is 1 else [7, 8]
            self.assertEqual(irf.width_dispersion, want)
            want = [] if i is 1 else [9, 10]
            self.assertEqual(irf.scale, want)
            self.assertTrue(irf.normalize)
            i = i + 1

    def test_k_matrices(self):
        self.assertTrue("km1" in self.model.k_matrices)
        self.assertTrue(np.array_equal(self.model.k_matrices["km1"]
                                       .asarray(),
                        np.array([[31, 33, 35, 37],
                                 [32, 0, 0, 0],
                                 [34, 0, 0, 0],
                                 [36, 0, 0, 0]]
                                 )
                                      )
                        )

    def test_shapes(self):

        self.assertTrue("shape1" in self.model.shapes)

        shape = self.model.shapes["shape1"]

        self.assertTrue(isinstance(shape, SpectralShapeGaussian))
        self.assertEqual(shape.amplitude, "shape.1")
        self.assertEqual(shape.location, "shape.2")
        self.assertEqual(shape.width, "shape.3")

    def test_megacomplexes(self):
        self.assertTrue(len(self.model.megacomplexes) is 3)

        i = 1
        for _ in self.model.megacomplexes:
            label = "cmplx{}".format(i)
            self.assertTrue(label in self.model.megacomplexes)
            megacomplex = self.model.megacomplexes[label]
            self.assertTrue(isinstance(megacomplex, KineticMegacomplex))
            self.assertTrue(megacomplex.label == label)
            self.assertTrue(megacomplex.k_matrices == ["km{}".format(i)])
            i = i + 1

    def test_compartment_constraints(self):
        self.assertTrue(len(self.model.compartment_constraints) is 4)

        self.assertTrue(any(isinstance(c, ZeroConstraint) for c in
                            self.model.compartment_constraints))

        zcs = [zc for zc in self.model.compartment_constraints
               if isinstance(zc, ZeroConstraint)]
        self.assertTrue(len(zcs) is 2)
        for zc in zcs:
            self.assertTrue(zc.compartment is 5)
            self.assertTrue(zc.intervals == [(1, 100), (2, 200)])

        self.assertTrue(any(isinstance(c, EqualConstraint) for c in
                            self.model.compartment_constraints))
        ec = [ec for ec in self.model.compartment_constraints
              if isinstance(ec, EqualConstraint)][0]
        self.assertTrue(ec.compartment is 5)
        self.assertTrue(ec.intervals == [(60, 700)])
        self.assertTrue(ec.target == 9)
        self.assertTrue(ec.parameter == 54)

        self.assertTrue(any(isinstance(c, EqualAreaConstraint) for c in
                            self.model.compartment_constraints))
        eac = [eac for eac in self.model.compartment_constraints
               if isinstance(eac, EqualAreaConstraint)][0]
        self.assertTrue(eac.compartment is 3)
        self.assertTrue(eac.intervals == [(670, 810)])
        self.assertTrue(eac.target == 1)
        self.assertTrue(eac.parameter == 55)
        self.assertTrue(eac.weight == 0.0016)

    def test_relations(self):
        self.assertTrue(len(self.model.relations) is 3)

        self.assertTrue(all(isinstance(r, Relation) for r in
                            self.model.relations))

        rel = [r for r in self.model.relations
               if r.parameter == 86][0]
        self.assertTrue(rel.to == {'const': 0, 89: 1, 90: 1, 87: -1.0})

        rel = [r for r in self.model.relations
               if r.parameter == 87][0]
        self.assertTrue(rel.to == {'const': 2.6, 83: 1, 84: 1, 81: -1.0})

        rel = [r for r in self.model.relations
               if r.parameter == 89][0]
        self.assertTrue(rel.to == {30: 1})

    def test_parameter_constraints(self):
        self.assertTrue(len(self.model.parameter_constraints) is 4)

        pc = self.model.parameter_constraints[0]
        self.assertTrue(isinstance(pc, FixedConstraint))
        self.assertEqual(pc.parameter, [1, 2, 3, 54])

        pc = self.model.parameter_constraints[1]
        self.assertTrue(isinstance(pc, FixedConstraint))
        self.assertEqual(pc.parameter, [1, 2, 3])

        pc = self.model.parameter_constraints[2]
        self.assertTrue(isinstance(pc, BoundConstraint))
        self.assertEqual(pc.parameter, list(range(100, 150)))
        self.assertEqual(pc.lower, 0)
        self.assertEqual(pc.upper, "NaN")

        pc = self.model.parameter_constraints[3]
        self.assertTrue(isinstance(pc, BoundConstraint))
        self.assertEqual(pc.parameter, list(range(100, 120)))
        self.assertEqual(pc.lower, "NaN")
        self.assertEqual(pc.upper, 7e-8)

    def test_parameter(self):
        self.assertTrue(len(self.model.parameter) is 3)

        self.assertTrue(all(isinstance(p, Parameter) for p in
                            self.model.parameter))

        par = [p for p in self.model.parameter
               if p.index == 1][0]
        self.assertTrue(par.value == 4.13e-02)

        par = [p for p in self.model.parameter
               if p.index == 2][0]
        self.assertTrue(par.value == 1)

        par = [p for p in self.model.parameter
               if p.index == 3][0]
        self.assertTrue(par.value == 1.78)
        self.assertTrue(par.label == "spectral_equality")

    def test_parameter_blocks(self):

        self.assertTrue("shape" in self.model.parameter_blocks)

        block = self.model.parameter_blocks["shape"]

        self.assertFalse(block.fit)
        self.assertEqual(block.parameter, [22, 33, 44])
        self.assertEqual(block.sub_blocks, None)

        self.assertTrue("nested" in self.model.parameter_blocks)

        block = self.model.parameter_blocks["nested"]

        self.assertTrue(block.fit)
        self.assertEqual(block.parameter, [])
        self.assertEqual(len(block.sub_blocks), 1)
        self.assertTrue("inner" in block.sub_blocks)

        block = block.sub_blocks["inner"]

        self.assertTrue(block.fit)
        self.assertEqual(block.parameter, [66])
        self.assertEqual(block.sub_blocks, None)
