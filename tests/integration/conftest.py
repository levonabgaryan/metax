import pytest

from backend.core.application.input_ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.di.boostrap import main_container
from backend.frameworks_and_drivers.di.main_container import MainContainer
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer


@pytest.fixture(scope="session")
def container() -> MainContainer:
    return main_container


@pytest.fixture
def unit_of_work(container: MainContainer) -> UnitOfWork:
    patterns: PatternsContainer = container.patterns.container
    return patterns.unit_of_work()
