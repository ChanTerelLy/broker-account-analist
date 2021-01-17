import json

from graphene_django.utils.testing import GraphQLTestCase

class AssetTestCase(GraphQLTestCase):

    def test_some_query(self):
        response = self.query(
            '''
            query($key: String!) {
                getTemplateByKey(key:$key) {
                    id
                }
            }
            ''',
            variables={'key': "template"}
        )

        content = json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)