#!/usr/bin/env python3

# ruff: noqa: I001

from openg2p_portal_api_common.app import (
    Initializer as SelfServicePortalCommonInitializer,
)
from openg2p_fastapi_common.ping import PingInitializer

main_init = SelfServicePortalCommonInitializer()
PingInitializer()

main_init.main()
