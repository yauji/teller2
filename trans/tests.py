import json

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import AnonymousUser, User
from django.http.request import HttpRequest

from trans.models import PmethodGroup, Pmethod, CategoryGroup, Category, Trans

from . import views
#from trans.views import CategoryUi


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
        
    def test_pmg_add_ok01(self):
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
        
    def test_pm_add_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)
        
        response = c.post('/t/pmgroup/add', {'name':'pmg1',\
                                             })
        pmgs = PmethodGroup.objects.all()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(pmgs), 1)

        #pm
        response = c.post('/t/pmethod/add', {'pmg':pmgs[0].id,\
                                             'name':'pm1'})
        pms = Pmethod.objects.all()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(pms), 1)
        self.assertEqual(pms[0].name, 'pm1')


        
class CategoryTestCase2(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)

        cg1 = CategoryGroup.objects.create(name='cg1')
        Category.objects.create(group=cg1, name='c11')
        Category.objects.create(group=cg1, name='c12')

        cg2 = CategoryGroup.objects.create(name='cg2')
        Category.objects.create(group=cg2, name='c21')
        Category.objects.create(group=cg2, name='c22')


    def test_cg_list_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)
        
        response = c.get('/t/categorygroup/1/list/')
        #print(response.content)
        #print(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200)

        dec = json.loads(response.content.decode("utf-8"))
        #print(dec['category_list'])
        self.assertEqual(len(dec['category_list']), 2)





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
        

class TransTestCase2(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)
        self.user = User.objects.create_user(username='test1', email='test@test.com',\
                                             password='password')

        pmg = PmethodGroup.objects.create(name='pmg1')
        Pmethod.objects.create(group=pmg, name='pm1')
        Pmethod.objects.create(group=pmg, name='pm12')

        cg = CategoryGroup.objects.create(name='cg1')
        Category.objects.create(group=cg, name='c1')
        Category.objects.create(group=cg, name='c12')


    def test_add_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)

        pms = Pmethod.objects.all()
        #print(pms)
        cs = Category.objects.all()

        #1st trans---
        print("item1--")
        response = c.post('/t/add', {'date': '2017/01/01', 'name': 'item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':100,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        #print(response.content)
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].name, 'item1')
        self.assertEqual(ts[0].balance, -100)


        #2nd trans---
        print("item2--")
        response = c.post('/t/add', {'date': '2017/01/03', 'name': 'item2',\
                                     'c':cs[1].id,\
                                     'pm':pms[0].id,\
                                     'expense':50,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        t = ts[1]
        self.assertEqual(t.balance, -150)

        #3rd trans---
        response = c.post('/t/add', {'date': '2017/01/02', 'name': 'item3',\
                                     'c':cs[1].id,\
                                     'pm':pms[1].id,\
                                     'expense':20,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        t = ts[2]
        self.assertEqual(t.balance, -20)

        #4th trans---
        response = c.post('/t/add', {'date': '2017/01/02', 'name': 'item4',\
                                     'c':cs[1].id,\
                                     'pm':pms[0].id,\
                                     'expense':40,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        t = ts[0]
        self.assertEqual(t.balance, -100)
        t = ts[3]
        self.assertEqual(t.balance, -140)
        t = ts[1]
        self.assertEqual(t.balance, -190)
        


    def test_add_pay4other_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)

        pms = Pmethod.objects.all()
        cs = Category.objects.all()

        #1st trans---
        print("item1--")
        response = c.post('/t/add', {'date': '2017/01/01', 'name': 'item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':100,\
                                     'memo':'memo1',\
                                     'share_type':3,\
                                     'user_pay4':'test1',\
        })
        #print(response.content)
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].name, 'item1')
        self.assertEqual(ts[0].balance, -100)
        self.assertEqual(ts[0].user_pay4.username, 'test1')



        
    def test_delete_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)

        pms = Pmethod.objects.all()
        cs = Category.objects.all()

        #1st trans---
        #print("item1--")
        response = c.post('/t/add', {'date': '2017/01/01', 'name': 'item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':100,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        #2nd trans---
        #print("item2--")
        response = c.post('/t/add', {'date': '2017/01/03', 'name': 'item2',\
                                     'c':cs[1].id,\
                                     'pm':pms[0].id,\
                                     'expense':50,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        #3rd trans---
        response = c.post('/t/add', {'date': '2017/01/02', 'name': 'item3',\
                                     'c':cs[1].id,\
                                     'pm':pms[1].id,\
                                     'expense':20,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        #print("delete item1,3--")
        response = c.post('/t/delete', {'tids': [1,3],\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].name, 'item2')
        self.assertEqual(ts[0].balance, -50)

    def test_list_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)

        pms = Pmethod.objects.all()
        #print(pms)
        cs = Category.objects.all()

        #1st trans---
        #print("item1--")
        response = c.post('/t/add', {'date': '2017/01/01', 'name': 'item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':100,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        #print(response.content)
        self.assertEqual(response.status_code, 302)

        response = c.get('/t/list')
        #print(response.content)
        #print(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200)


        # list method---
        req = response.wsgi_request

        #req.user = USER
        #req.is_authenticated = "True"
        res = views.list(req)
        print(res.content)

        
        

        



        
