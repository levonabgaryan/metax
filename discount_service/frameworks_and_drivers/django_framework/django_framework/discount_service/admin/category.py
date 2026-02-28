import uuid

from asgiref.sync import async_to_sync
from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render

from discount_service.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from discount_service.core.application.commands_handlers.category.add_new_helper_words import (
    AddNewHelperWordsCommandHandler,
    AddNewHelperWordsCommand,
)
from discount_service.frameworks_and_drivers.di import get_service_container


class CategoryAdminHandler:
    def __init__(self, admin_site: AdminSite):
        self.admin_site = admin_site

    def add_view(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            category_name = request.POST.get("category_name")
            helper_words = request.POST.getlist("helper_words")

            if category_name and helper_words:
                async_to_sync(self._create_category)(category_name, helper_words)
                return redirect("admin:index")

        context = {
            **self.admin_site.each_context(request),
            "title": "Add Category",
            "app_label": "discount_core",
        }
        return render(request, "admin/category/add.html", context)

    @staticmethod
    async def _create_category(category_name: str, helper_words: list[str]) -> None:
        unit_of_work = await get_service_container().patterns_container.container.unit_of_work.async_()
        event_bus = await get_service_container().patterns_container.container.event_bus.async_()

        command = CreateCategoryCommand(
            category_uuid=uuid.uuid4(), name=category_name, helper_words=frozenset(helper_words)
        )
        command_handler = CreateCategoryCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
        await command_handler.handle_command(command)

    @staticmethod
    async def _add_new_helper_words(category_name: str, new_helper_words: list[str]) -> None:
        unit_of_work = await get_service_container().patterns_container.container.unit_of_work.async_()
        event_bus = await get_service_container().patterns_container.container.event_bus.async_()

        async with unit_of_work as uow:
            category = await uow.category_repo.get_by_name(category_name)

        command = AddNewHelperWordsCommand(
            category_uuid=category.get_uuid(),
            new_helper_words=frozenset(new_helper_words),
        )
        command_handler = AddNewHelperWordsCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
        await command_handler.handle_command(command)
