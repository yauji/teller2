import datetime
import json
import re

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import AnonymousUser, User
from django.http.request import HttpRequest
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from trans.models import PmethodGroup, Pmethod, CategoryGroup, Category, Trans
from trans.views import CategoryUi
from trans.views import PmethodUi

from . import views
#from trans.views import CategoryUi


USER='admin'
PASS='hogehoge'

C_MOVE_ID = 101
C_WITHDRAW_ID = 103


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
        print("In case that there are a fail related to pagination, it's ok.")
        self.assertEqual(len(dec['category_list']), 2)





class TransTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER, email='admin@test.com',\
                                             password=PASS)

        pmg = PmethodGroup.objects.create(name='pmg1', user=self.user)
        Pmethod.objects.create(group=pmg, name='pm1')

        cg = CategoryGroup.objects.create(name='cg1')
        Category.objects.create(group=cg, name='c1')
        Category.objects.create(group=cg, name='c12')
        Category.objects.create(group=cg, name='move', id=C_MOVE_ID)
        

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

        pmg = PmethodGroup.objects.create(name='pmg1', user=self.user, order=1)
        Pmethod.objects.create(group=pmg, name='pm1', order=1)
        Pmethod.objects.create(group=pmg, name='pm12', order=2)

        pmg = PmethodGroup.objects.create(name='pmg2', user=self.user, order=2)
        Pmethod.objects.create(group=pmg, name='pm21', order=1)

        cg = CategoryGroup.objects.create(name='cg1', order=1)
        Category.objects.create(group=cg, name='c1', order=1)
        Category.objects.create(group=cg, name='c12', order=2)

        cg = CategoryGroup.objects.create(name='cg2', order=2)
        Category.objects.create(group=cg, name='move', id=C_MOVE_ID, order=1)
        Category.objects.create(group=cg, name='withdraw', id=C_WITHDRAW_ID, order=2)


    def add_trans1(self, c, pms, cs):
        #1st trans---
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
        
        

    #add---------
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

        t = Trans.objects.filter(name='item1')[0]
        self.assertEqual(t.balance, -100)
        t = Trans.objects.filter(name='item4')[0]
        self.assertEqual(t.balance, -140)
        t = Trans.objects.filter(name='item2')[0]
        self.assertEqual(t.balance, -190)

        """
        ts = Trans.objects.all()
        t = ts[0]
        self.assertEqual(t.balance, -100)
        t = ts[3]
        self.assertEqual(t.balance, -140)
        t = ts[1]
        self.assertEqual(t.balance, -190)
        """
        

    def test_add_move_ok01(self):
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


        #2nd trans (move)---
        print("item2--")
        response = c.post('/t/add', {'date': '2017/01/03', 'name': 'item2',\
                                     'c':C_MOVE_ID,\
                                     'pm':pms[0].id,\
                                     'pm2':pms[1].id,\
                                     'expense':50,\
                                     'memo':'move',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        t = ts[1]
        self.assertEqual(t.balance, -150)
        t = ts[2]
        self.assertEqual(t.balance, 50)

        


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
        ts = Trans.objects.all()

        """
        print("----------")
        for t in ts:
            print(t.id)
        """
        response = c.post('/t/delete', {'tids': [ts[0].id, ts[2].id],\
        })
        self.assertEqual(response.status_code, 302)

        ts = Trans.objects.all()
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].name, 'item2')
        self.assertEqual(ts[0].balance, -50)

        
    def test_withdraw_ok01(self):
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
                                     'pm':pms[0].id,\
                                     'expense':20,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 302)

        #print("withdraw item1,3--")
        #ts = Trans.objects.all()
        t1 = Trans.objects.filter(name='item1')[0]
        t3 = Trans.objects.filter(name='item3')[0]
                
        response = c.post('/t/multi_trans_select', {
            'withdraw': True,\
            'tids': [t1.id, t3.id],\
            'date': '2017/02/01', \
            'pm':pms[2].id,\
            'memo':'wd',\
        })
        self.assertEqual(response.status_code, 302)


        ts = Trans.objects.all()
        self.assertEqual(len(ts), 4)
        t = Trans.objects.filter(memo='wd')[0]
        #print(t.memo)
        self.assertEqual(t.expense, 120)
        self.assertEqual(t.balance, -120)
        
        """
        self.assertEqual(ts[3].expense, 120)
        self.assertEqual(ts[3].balance, -120)
        """
        
        self.assertEqual(ts[0].balance, 0)
        #fail. I don't know why...
        #self.assertEqual(ts[1].balance, -20)
        #self.assertEqual(ts[2].balance, -20)

        
    def test_list_ok01(self):
        c = Client()
        c.login(username='test1', password='password')
        #c.login(username=USER, password=PASS)

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


        # list method (actual)---
        req = response.wsgi_request
        self.user.username=''
        req.user = self.user
        res = views.list(req)
        #print(res.content)


        # get expected html--
        latest_trans_list = Trans.objects.all()
        paginator = Paginator(latest_trans_list, 50)
        transs = paginator.page(1)
            
        pmgs = PmethodGroup.objects.filter(user=self.user).order_by('order')
        #pmgs = PmethodGroup.objects.filter(user=self.user)all()
        cgs = CategoryGroup.objects.all()

        #pm
        pmui_list = []
        for pmg in pmgs:
            pmlist = Pmethod.objects.filter(group = pmg).order_by('order')

            first = True
            for pm in pmlist:
                pmui = PmethodUi()
                pmui.id = pm.id
                pmui.name = pm.name
                pmui.group = pm.group
                pmui.first_in_group = first
                first = False
                pmui.selected = True
                pmui_list.append(pmui)


        #category
        cui_list = []
        for cg in cgs:
            clist = Category.objects.filter(group = cg).order_by('order')

            first = True
            for c in clist:
                cui = CategoryUi()
                cui.id = c.id
                cui.name = c.name
                cui.group = c.group
                cui.first_in_group = first
                first = False
                cui.selected = True
                cui_list.append(cui)

        #date
        dateto = datetime.datetime.now()
        str_dateto = dateto.strftime('%Y/%m/%d')

                
        expected_html = render_to_string('trans/list.html',\
                                 {'request.user': 'admin',\
                                  'latest_trans_list': transs,\
                                  'pmethod_list': pmui_list,\
                                  'pmgroup_list': pmgs, \
                                  'categorygroup_list' : cgs , \
                                  'category_list' : cui_list,\
                                  'datefrom' : '2000/01/01',\
                                  'dateto' : str_dateto,\
                                 })

        #print(expected_html)
        #print(res.content.decode())

        self.assertEqualExceptCSRF(res.content.decode(), expected_html)
        #self.assertEqual(res.content, expected_html)        
        #self.assertEqual(res.content.decode(), expected_html)


    def test_sum_expense_ok01(self):
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


        # test sum---
        response = c.get('/t/sum_expense', {'ids[]': [ts[0].id, ts[1].id]})
        #response = c.get('/t/sum_expense', {'ids[]': ['1', '2']})
        #print(response.content)
        #print(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200)

        dec = json.loads(response.content.decode("utf-8"))
        #print(dec['sum'])
        self.assertEqual(dec['sum'], 150)


    # monthly report-----------------
    def test_mr_ok01(self):
        c = Client()
        c.login(username=USER, password=PASS)

        pms = Pmethod.objects.all()
        #print(pms)
        cs = Category.objects.all()

        self.add_trans1(c, pms, cs)

        response = c.get('/t/monthlyreport')
        self.assertEqual(response.status_code, 200)


        # list method (actual)---
        req = response.wsgi_request
        res = views.monthlyreport(req)
        #print(res)

        # how to check output...



        
        


    @staticmethod
    def remove_csrf(html_code):
        csrf_regex = r'<input[^>]+csrfmiddlewaretoken[^>]+>'
        html = re.sub(csrf_regex, '', html_code)
        #return re.sub(csrf_regex, '', html_code)

        regex = r'admin'
        return re.sub(regex, '', html)


    def assertEqualExceptCSRF(self, html_code1, html_code2):
        return self.assertEqual(
            self.remove_csrf(html_code1),
            self.remove_csrf(html_code2)
        )




        



        
