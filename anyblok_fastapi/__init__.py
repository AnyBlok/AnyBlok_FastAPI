# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
def anyblok_init_config(unittest: bool = False):
    from anyblok import config as anyblok_config  # noqa import anyblok.config
    from anyblok_fastapi import (  # noqa import config definition
        config as anyblok_fastapi_config,
    )
