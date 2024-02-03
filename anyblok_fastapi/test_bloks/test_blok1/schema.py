# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pydantic import BaseModel, ConfigDict


class ExampleCreateSchema(BaseModel):
    name: str


class ExampleSchema(ExampleCreateSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
