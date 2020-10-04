def anyblok_init_config(unittest: bool = False):
    from anyblok import config as anyblok_config  # noqa import anyblok.config
    from anyblok_fastapi import (  # noqa import config definition
        config as anyblok_fastapi_config,
    )
