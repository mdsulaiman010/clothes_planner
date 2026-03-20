from tryon.base import TryOnProvider
from tryon.fashn_provider import FashnAiProvider
from tryon.local_provider import LocalProvider

_providers = {
    'fashn': FashnAiProvider,
    'local': LocalProvider,
}


def get_tryon_provider(name: str = 'fashn') -> TryOnProvider:
    provider_cls = _providers.get(name)
    if not provider_cls:
        raise ValueError(f"Unknown try-on provider: {name}. Available: {list(_providers.keys())}")
    return provider_cls()
