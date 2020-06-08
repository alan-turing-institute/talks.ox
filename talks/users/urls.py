from django.conf.urls import url

from talks.users.views import (manage_collections, list_public_collections, browse_public_collections, view_collection, add_collection, edit_collection, delete_collection, my_talks)


urlpatterns = [
    url(r'^lists$', manage_collections, name='manage-lists'),
    url(r'^mytalks$', my_talks, name='my-talks'),
    url(r'^lists/public$', list_public_collections, name='view-public-lists'),
    url(r'^lists/browse-public$', browse_public_collections, name='list-public-lists'),
    url(r'^lists/new$', add_collection, name='add-list'),
    url(r'^lists/id/(?P<collection_slug>[^/]+)/$', view_collection, name='view-list'),
    url(r'^lists/id/(?P<collection_slug>[^/]+)/edit$', edit_collection, name='edit-list'),
    url(r'^lists/id/(?P<collection_slug>[^/]+)/delete', delete_collection, name='delete-list'),
]
