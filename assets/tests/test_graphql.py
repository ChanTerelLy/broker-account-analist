import json
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase
from assets.models import *
from graphene_django.utils.testing import graphql_query
from django.contrib.auth.models import User


class AssetQueryTest(GraphQLTestCase):
    def setUp(self):
        self.username = 'john'
        self.password = 'secret123'
        self.email = 'john@doe.com'
        self.url = reverse('assets')
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.account = Account.objects.create(user=self.user, name='testAccount', amount=100000)
        self.template = Template.objects.create(name='testTemplate', description='', url='test.com', key='template')

    def test_get_template_by_key_query(self):
        response = self.query(
            '''
            query($key: String!) {
                getTemplateByKey(key:$key) {
                    name
                }
            }
            ''',
            variables={'key': "template"}
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual('testTemplate', content['data']['getTemplateByKey'][0]['name'])

    def test_user_accounts_query(self):
        response = graphql_query(
            '''
            query{
              userAccounts{
                name
              }
            }
            ''',
            client=self.client
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual('testAccount', content['data']['userAccounts'][0]['name'])