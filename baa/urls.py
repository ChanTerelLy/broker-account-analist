from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from graphene_file_upload.django import FileUploadGraphQLView
from django.contrib.auth.mixins import LoginRequiredMixin
from graphene_django.views import GraphQLView


class PrivateGraphQLView(FileUploadGraphQLView, LoginRequiredMixin, GraphQLView):
    pass

urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    url(r'^graphql', PrivateGraphQLView.as_view(graphiql=True)),
    path('', include('assets.urls')),
    path('', include('accounts.urls')),
]
