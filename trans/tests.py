from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import AnonymousUser, User

from trans.models import PmethodGroup

USER='admin'
PASS='hogehoge'

class TransTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)

    def test_login(self):
        c = Client()
        response = c.post('/login/', {'username': USER, 'password': PASS})
        #print(response.status_code)
        print(response.content)
        self.assertEqual(response.status_code, 200)

    def test_show_trans(self):
        c = Client()
        c.login(username=USER, password=PASS)
        response = c.post('/t/pmethod', {'username': USER, 'password': PASS})
        response = c.post('/t/', {'username': USER, 'password': PASS})
        #print(response.status_code)
        #print(response.content)
        self.assertEqual(response.status_code, 200)

        
