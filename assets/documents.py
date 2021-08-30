from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from .models import CorpBound


@registry.register_document
class BoundDocument(Document):
    class Index:
        # Name of the Elasticsearch index
        name = 'bond'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = CorpBound  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'name',
            'short_name',
            'isin',
            'last_price',
        ]
