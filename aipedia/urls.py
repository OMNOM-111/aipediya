from django.contrib import admin
from django.urls import path
from catalog import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("models/<slug:slug>", views.detail, name="detail"),
    path("tools/<slug:slug>", views.tool_detail, name="tool_detail"),
    path("privacy", views.privacy, name="privacy"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("ads.txt", views.ads_txt, name="ads_txt"),
    path("indexnow/<str:key>.txt", views.indexnow_key, name="indexnow_key"),
    path("healthz", views.health, name="health"),
    path("releases/20260920/acceptance.zip", views.release_acceptance, name="release_acceptance"),
    path("admin/", admin.site.urls),
]
