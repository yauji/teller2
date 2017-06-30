from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import AnonymousUser, User

from trans.models import PmethodGroup

USER='admin'
PASS='hogehoge'

class PmethodTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)

    def test_show_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)
        response = c.post('/t/pmethod')
        #response = c.post('/t/pmethod', {'username': USER, 'password': PASS})
        #print(response.status_code)
        #print(response.content)
        self.assertEqual(response.status_code, 200)
        
    def test_add_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)
        response = c.post('/t/pmgroup/add', {'name':'pmg1',\
                                             })
        #print(response.status_code)
        #print(response.content)
        pmgs = PmethodGroup.objects.all()
        #print(pmgs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(pmgs), 1)
        self.assertEqual(pmgs[0].name, 'pmg1')
        



class TransTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)

    def test_login(self):
        c = Client()
        response = c.post('/')
        #response = c.post('/login/', {'username': USER, 'password': PASS})
        #print(response.status_code)
        #print(response.content)
        self.assertEqual(response.status_code, 302)

    def test_show_trans(self):
        c = Client()
        c.login(username=USER, password=PASS)
        #response = c.post('/t/pmethod', {'username': USER, 'password': PASS})
        response = c.post('/t/', {'username': USER, 'password': PASS})
        #print(response.status_code)
        #print(response.content)
        self.assertEqual(response.status_code, 200)
        

        
        
