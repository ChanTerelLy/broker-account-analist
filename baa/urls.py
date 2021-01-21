from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView
import asyncio

from graphql.execution.executors.asyncio import AsyncioExecutor

executor = AsyncioExecutor(loop=asyncio.get_event_loop())
urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    url(r'^graphql', FileUploadGraphQLView.as_view(graphiql=True)),
    path('', include('assets.urls')),
    path('', include('accounts.urls')),
]
