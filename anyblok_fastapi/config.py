# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2026 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Configuration options for AnyBlok FastAPI (delegated to anyblok-starlette)."""

from anyblok_starlette.config import get_db_name

__all__ = ["get_db_name"]
