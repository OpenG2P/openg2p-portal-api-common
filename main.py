#!/usr/bin/env python3

# ruff: noqa: I001

from openg2p_portal_api_common.app import Initializer as SelfServicePortalInitializer
from openg2p_fastapi_common.ping import PingInitializer

main_init = SelfServicePortalInitializer()
PingInitializer()

main_init.main()
