from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from graphene_file_upload.django import FileUploadGraphQLView
from django.contrib.auth.mixins import LoginRequiredMixin
from graphene_django.views import GraphQLView


class PrivateGraphQLView(FileUploadGraphQLView, GraphQLView):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and request.headers['x-api-auth'] != settings.INTERNAL_API_TOKEN:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    url(r'^graphql', PrivateGraphQLView.as_view(graphiql=True)),
    path('', include('assets.urls')),
    path('', include('accounts.urls')),
]
