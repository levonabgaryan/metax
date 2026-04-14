from __future__ import annotations

import logging

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from .patterns_container import PatternsContainer
from .repositories_container import RepositoriesContainer
from .resources import async_opensearch_client_resource

logger = logging.getLogger(__name__)


class MetaxContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    opensearch_async_client: providers.Resource[AsyncOpenSearch] = providers.Resource(
        async_opensearch_client_resource,
        host=config.opensearch_host,
        port=config.opensearch_port,
        user=config.opensearch_user,
        password=config.opensearch_password,
        verify_certs=config.opensearch_verify_certs,
    )
    repositories_container: providers.Container[RepositoriesContainer] = providers.Container(
        RepositoriesContainer, opensearch_async_client=opensearch_async_client
    )
    patterns_container: providers.Container[PatternsContainer] = providers.Container(
        PatternsContainer, repositories_container=repositories_container
    )
