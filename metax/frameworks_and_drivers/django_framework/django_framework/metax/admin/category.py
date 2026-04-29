from asgiref.sync import async_to_sync
from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render

from metax.core.application.cud_services.category import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsService,
    CreateCategoryRequestDTO,
    CreateCategoryService,
    DeleteHelperWordsRequestDTO,
    DeleteHelperWordsService,
)
from metax.core.application.cud_services.category.dtos import HelperWordPayload as AddHelperWordPayload
from metax.core.application.cud_services.category.dtos import HelperWordPayload as CreateHelperWordPayload
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax_bootstrap import get_metax_lifespan_manager


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
        di_container = get_metax_lifespan_manager().get_di_container()
        patterns = di_container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await di_container.resources_container.container.event_bus.async_()

        request_dto = CreateCategoryRequestDTO(
            name=category_name,
            helper_words_payload=[CreateHelperWordPayload(text=helper_word) for helper_word in helper_words],
        )
        service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        await service.execute(request_dto)

    @staticmethod
    async def __add_new_helper_words(category_name: str, new_helper_words: list[str]) -> None:
        di_container = get_metax_lifespan_manager().get_di_container()
        patterns = di_container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await di_container.resources_container.container.event_bus.async_()

        uow = await unit_of_work_provider.provide()
        async with uow:
            category = await uow.category_repo.get_by_name(category_name)

        service = AddNewHelperWordsService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        for helper_word in new_helper_words:
            command = AddNewHelperWordsRequestDTO(
                category_uuid=category.get_uuid(),
                new_helper_word_payload=AddHelperWordPayload(text=helper_word),
            )
            await service.execute(command)

    @staticmethod
    async def __delete_helper_words(category_name: str, words_to_delete: list[str]) -> None:
        di_container = get_metax_lifespan_manager().get_di_container()
        patterns = di_container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await di_container.resources_container.container.event_bus.async_()

        uow = await unit_of_work_provider.provide()
        async with uow:
            category = await uow.category_repo.get_by_name(category_name)

        request_dto = DeleteHelperWordsRequestDTO(
            category_uuid=category.get_uuid(),
            helper_words_uuid=[
                helper_word.get_uuid()
                for helper_word in category.get_helper_words()
                if helper_word.get_text() in words_to_delete
            ],
        )
        service = DeleteHelperWordsService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        await service.execute(request_dto)

    @staticmethod
    async def __get__all_categories() -> list[Category]:
        di_container = get_metax_lifespan_manager().get_di_container()
        patterns = di_container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        uow = await unit_of_work_provider.provide()
        async with uow:
            all_categories = await uow.category_repo.all()
        return all_categories

    @staticmethod
    def __convert_category_to_dict(category: Category) -> dict[str, str | list[str]]:
        return {
            "category_uuid": str(category.get_uuid()),
            "category_name": category.get_name(),
            "helper_words": [helper_word.get_text() for helper_word in category.get_helper_words()],
        }
