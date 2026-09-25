from django.contrib import admin
from django.urls import path, re_path
from catalog import views, product_history

# Language-neutral URLconf. English is served unprefixed; every other locale
# reaches the same patterns through catalog.middleware.LanguageMiddleware,
# which strips the /<locale>/ prefix from path_info (see catalog/locale_urls.py
# for the list of localized pages). Build public links with locale_urls, never
# by concatenating prefixes by hand.
urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("tools/", views.tool_catalog, name="tool_catalog"),
    path("models/<slug:slug>", views.detail, name="detail"),
    path("tools/<slug:slug>", views.tool_detail, name="tool_detail"),
    path("methodology", views.methodology, name="methodology"),
    path("privacy", views.privacy, name="privacy"),
    path("history/", product_history.history, name="product_history"),
    path("history/source/<slug:slug>", product_history.history_source, name="product_history_source"),
    path("collections/", views.collections_index, name="collections"),
    path("collections/<slug:slug>", views.collection, name="collection"),
    path("datasets/", views.datasets_index, name="datasets"),
    re_path(r"^datasets/(?P<kind>models|tools)$", views.dataset_page, name="dataset_page"),
    # Language-neutral endpoints.
    path("datasets/manifest.json", views.dataset_manifest, name="dataset_manifest"),
    re_path(r"^datasets/(?P<slug>[a-z0-9-]+)\.(?P<fmt>json|csv)$", views.dataset_download, name="dataset_download"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    re_path(r"^sitemaps/(?P<code>[a-z-]+)\.xml$", views.sitemap_locale, name="sitemap_locale"),
    path("ads.txt", views.ads_txt, name="ads_txt"),
    path("indexnow/<str:key>.txt", views.indexnow_key, name="indexnow_key"),
    path("healthz", views.health, name="health"),
    path("releases/20260920/acceptance.zip", views.release_acceptance, name="release_acceptance"),
    path("admin/", admin.site.urls),
]

handler404 = "catalog.views.handler404"
