# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""demo Example model, this model is goging to create table at startup
"""
from anyblok import Declarations
from anyblok.column import Integer, String

Model = Declarations.Model


@Declarations.register(Model)
class Example:
    """Example Model, see more column field
    http://anyblok.readthedocs.io/en/latest/MEMENTO.html#column
    """

    id = Integer(primary_key=True)
    name = String(label="Name", unique=True, nullable=False)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"<Example: {self.name}, {self.id}>"
