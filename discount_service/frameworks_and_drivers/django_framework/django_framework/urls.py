"""
URL configuration for django_framework project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from adrf import routers

from django_framework.discount_service.admin.site import admin_site
from django_framework.discount_service.views.health import HealthCheckView
from django_framework.discount_service.views.category import CategoryViewSet
from django_framework.discount_service.views.discounted_product import DiscountedProductViewSet

router = routers.DefaultRouter()
router.register(r"category", CategoryViewSet, basename="category")
router.register(r"discounted-product", DiscountedProductViewSet, basename="discounted-product")

urlpatterns = [
    path("admin/", admin_site.urls),
    path("healthcheck/", HealthCheckView.as_view()),
]

urlpatterns += router.urls
