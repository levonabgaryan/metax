from typing import Any, Union, override

from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


class Command(BaseCommand):
    help = "Shows all api urls"

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("🔍 List of all endpoints:"))
        resolver = get_resolver()
        self.print_urls(resolver.url_patterns)

    def print_urls(self, patterns: list[Union[URLResolver, URLPattern]], prefix: str = "") -> None:
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                new_prefix = prefix + str(pattern.pattern)
                self.print_urls(pattern.url_patterns, new_prefix)
            elif isinstance(pattern, URLPattern):
                full_path = prefix + str(pattern.pattern)
                clean_path = full_path.replace("^", "").replace("$", "")

                view_callback = pattern.callback
                actions = []

                if hasattr(view_callback, "initkwargs"):
                    method_map = view_callback.initkwargs.get("actions")
                    if method_map:
                        actions = [f"[{k.upper()} -> {v}]" for k, v in method_map.items()]

                if not actions and hasattr(view_callback, "actions"):
                    method_map = view_callback.actions
                    actions = [f"[{k.upper()} -> {v}]" for k, v in method_map.items()]

                action_str = " ".join(actions) if actions else f"({view_callback.__name__})"

                self.stdout.write(f"🔗 /{clean_path: <40} {self.style.WARNING(action_str)}")
