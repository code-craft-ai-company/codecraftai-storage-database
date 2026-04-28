"""
.. module:: mixins
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Contains mixins which can add generic functionality for Model objects.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []
__version__ = "1.0.0"

import json

from sqlalchemy import inspect

class SerializableMixIn:
    """
        Mixin style class that adds serialization to data model objects.
    """

    def as_dict(self):
        """
            Iterates the formal data attributes of a model and outputs a dictionary
            with the data based on the model.
        """
        dval = {}

        model = type(self)
        mapper = inspect(model)
        for col in mapper.attrs:
            col_key = col.key
            dval[col_key] = str(getattr(self, col_key))

        return dval


    def to_json(self, indent=4):
        """
            Iterates the formal data attributes of a model and creates a dictionary
            with the data based on the model, then converts the dictionary to a
            JSON string.
        """
        model_dict = self.as_dict()
        json_str = json.dumps(model_dict, indent=indent)
        return json_str
