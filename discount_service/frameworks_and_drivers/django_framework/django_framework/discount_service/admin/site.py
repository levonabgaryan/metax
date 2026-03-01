from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.http import HttpRequest
from django.urls import path, URLPattern, URLResolver

from django_framework.discount_service.admin.category import CategoryAdminHandler


class DiscountAdminSite(admin.AdminSite):
    site_header = "Discount Service Administration"
    index_title = "Discount service admin panel"

    def get_urls(self) -> list[URLPattern | URLResolver]:
        urls = super().get_urls()
        category_handler = CategoryAdminHandler(self)

        custom_urls = [
            path("categories/", self.admin_view(category_handler.all_categories), name="categories_list"),
            path("categories/add/", self.admin_view(category_handler.add_category), name="category_add"),
            path(
                "categories/delete-helper-words",
                self.admin_view(category_handler.delete_helper_words),
                name="category_delete_helper_words",
            ),
        ]
        return custom_urls + urls

    def get_app_list(self, request: HttpRequest, app_label: str | None = None) -> list[Any]:
        app_list = super().get_app_list(request, app_label)

        custom_app = {
            "name": "Main",
            "app_label": "discount_core",
            "app_url": "#",
            "has_module_perms": True,
            "models": [
                {
                    "name": "Categories",
                    "object_name": "category",
                    "admin_url": "/admin/categories/",
                    "view_only": True,
                },
            ],
        }

        app_list.insert(0, custom_app)
        return app_list


admin_site = DiscountAdminSite(name="discount_admin")
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
