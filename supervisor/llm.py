"""Supervisor LLM client: wraps raw _generate_response for unscrubbed output.

Used by FR-1, FR-2 (opt-in ranking), FR-4, FR-8, FR-10.
Provider and fallback are config-only (FR-14): the primary provider comes from
`[app].llm_provider`, and on primary failure one re-attempt runs with
`[app].llm_fallback_provider`. No scrubbing: JSON, `#`, and arrays survive.
"""

from loguru import logger

from app.config import config as app_config
from app.services.llm import _fallback_app_config, _generate_response


def _is_failed_response(response) -> bool:
    """_generate_response 把 Provider 失败返回为 "Error: ..." 文本；空串同样算失败。"""
    if not response or not response.strip():
        return True
    return response.startswith("Error: ")


def complete(system: str, user: str) -> str:
    """Call LLM with system + user prompts, return raw string (no scrubbing)."""
    prompt = f"{system}\n\n{user}"

    # 扁平的 [app] 分区快照（与 config.app 同构）；Provider 的 key/model/base_url
    # 全部由 _generate_response 按 Registry 解析，切换 Provider 只改配置。
    cfg_dict = dict(app_config.app)

    response = _generate_response(prompt, cfg_dict)

    if _is_failed_response(response):
        # FR-14: 主 Provider 失败时用配置的 fallback Provider 重新尝试一次；
        # fallback 的 model/base_url/api_key 来自它自己的 {provider}_* 键。
        fallback_config = _fallback_app_config(cfg_dict)
        if fallback_config is not None:
            logger.info(
                f"supervisor LLM primary provider failed, one re-attempt with "
                f"fallback provider '{fallback_config['llm_provider']}'"
            )
            response = _generate_response(prompt, fallback_config)

    return response or ""
