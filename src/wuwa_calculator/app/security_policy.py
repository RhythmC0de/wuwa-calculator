"""Compatibility shim: the policy now lives in infrastructure.url_policy."""

from wuwa_calculator.infrastructure.url_policy import (  # noqa: F401
    ALLOWED_REMOTE_HOSTS,
    allows_gacha_api,
    allows_local_image,
    allows_remote_content,
)
