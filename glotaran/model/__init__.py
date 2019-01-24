"""Glotaran Model Package

This package contains the Glotaran's base model object, the model decorators and
common model items.
"""

from . import (
    base_model,
    dataset_descriptor,
    model,
    model_item,
)

# Dataset

DatasetDescriptor = dataset_descriptor.DatasetDescriptor

# BaseModel

BaseModel = base_model.BaseModel

# Decorators

model = model.model
model_item_typed = model_item.model_item_typed
model_item = model_item.model_item


class ModelError(Exception):
    def __init__(self, model):

        msg = "Model Error\n"
        msg += "-----------\n\n"
        msg += "Please fix the following issues:\n"
        for error in model.errors():
            msg += f"* {error}\n"

        # Call the base class constructor with the parameters it needs
        super().__init__(msg)
