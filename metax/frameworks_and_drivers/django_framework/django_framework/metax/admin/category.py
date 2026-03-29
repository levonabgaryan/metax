import uuid

from asgiref.sync import async_to_sync
from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render

from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.core.application.commands_handlers.category.add_new_helper_words import (
    AddNewHelperWordsCommandHandler,
    AddNewHelperWordsCommand,
)
from metax.core.application.commands_handlers.category.delete_helper_words import (
    DeleteHelperWordsCommand,
    DeleteHelperWordsCommandHandler,
)
from metax.core.domain.entities.category.entity import Category
from metax.frameworks_and_drivers.di.metax_container import get_metax_container


class CategoryAdminHandler:
    def __init__(self, admin_site: AdminSite):
        super().__init__()
        self.__admin_site = admin_site

    def add_category(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            category_name = request.POST.get("category_name")
            helper_words = request.POST.getlist("helper_words")

            if category_name and helper_words:
                async_to_sync(self.__create_category)(category_name, helper_words)
                return redirect("admin:index")

        context = {
            **self.__admin_site.each_context(request),
            "title": "Add Category",
        }
        return render(request, "admin/category/add.html", context)

    def all_categories(self, request: HttpRequest) -> HttpResponse:
        categories = async_to_sync(self.__get__all_categories)()

        categories_data = [self.__convert_category_to_dict(category) for category in categories]

        context = {
            **self.__admin_site.each_context(request),
            "title": "Categories",
            "categories": categories_data,
        }

        return render(request, "admin/category/list.html", context)

    def delete_helper_words(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            category_name = request.POST.get("category_name")
            words_to_delete = request.POST.getlist("words_to_delete")

            if category_name and words_to_delete:
                async_to_sync(self.__delete_helper_words)(category_name, words_to_delete)

            return redirect("admin:categories_list")

        return render(request, "admin/category/delete_helper_words.html")

    def add_new_helper_words(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            category_name = request.POST.get("category_name")
            new_helper_words = request.POST.getlist("new_helper_words")

            if category_name and new_helper_words:
                async_to_sync(self.__add_new_helper_words)(category_name, new_helper_words)
            return redirect("admin:categories_list")
        return render(request, "admin/category/add_new_helper_words.html")

    # def update_category(self, request: HttpRequest) -> HttpResponse:
    #     if request.method == "POST":
    #         pass

    @staticmethod
    async def __create_category(category_name: str, helper_words: list[str]) -> None:
        container = get_metax_container().patterns_container.container
        unit_of_work_provider = await container.unit_of_work_provider.async_()
        event_bus = container.event_bus()

        command = CreateCategoryCommand(
            category_uuid=uuid.uuid4(), name=category_name, helper_words=frozenset(helper_words)
        )
        command_handler = CreateCategoryCommandHandler(
            unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
        )
        await command_handler.handle_command(command)

    @staticmethod
    async def __add_new_helper_words(category_name: str, new_helper_words: list[str]) -> None:
        container = get_metax_container().patterns_container.container
        unit_of_work_provider = await container.unit_of_work_provider.async_()
        event_bus = container.event_bus()

        uow = await unit_of_work_provider.create()
        async with uow:
            category = await uow.category_repo.get_by_name(category_name)

        command = AddNewHelperWordsCommand(
            category_uuid=category.get_uuid(),
            new_helper_words=frozenset(new_helper_words),
        )
        command_handler = AddNewHelperWordsCommandHandler(
            unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
        )
        await command_handler.handle_command(command)

    @staticmethod
    async def __delete_helper_words(category_name: str, words_to_delete: list[str]) -> None:
        container = get_metax_container().patterns_container.container
        unit_of_work_provider = await container.unit_of_work_provider.async_()
        event_bus = container.event_bus()

        uow = await unit_of_work_provider.create()
        async with uow:
            category = await uow.category_repo.get_by_name(category_name)

        command = DeleteHelperWordsCommand(
            category_uuid=category.get_uuid(),
            words_to_delete=frozenset(words_to_delete),
        )
        command_handler = DeleteHelperWordsCommandHandler(
            unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
        )
        await command_handler.handle_command(command)

    @staticmethod
    async def __get__all_categories() -> list[Category]:
        container = get_metax_container().patterns_container.container
        unit_of_work_provider = await container.unit_of_work_provider.async_()
        uow = await unit_of_work_provider.create()
        async with uow:
            all_categories = await uow.category_repo.get_all()
        return all_categories

    @staticmethod
    def __convert_category_to_dict(category: Category) -> dict[str, str | list[str]]:
        return {
            "category_uuid": str(category.get_uuid()),
            "category_name": category.get_name(),
            "helper_words": list(category.get_helper_words()),
        }
