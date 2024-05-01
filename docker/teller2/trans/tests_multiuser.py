import datetime
from datetime import timedelta
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
from trans.views import MonthlyreportEachMonthUi


from . import views
#from trans.views import CategoryUi


USER1='admin'
PASS1='hogehoge'

USER2='user2'
PASS2='hogehoge'

C_MOVE_ID = 101
C_WITHDRAW_ID = 110
#C_WITHDRAW_ID = 103

class TransTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username=USER1, email='admin@test.com',\
                                              password=PASS1)
        self.user2 = User.objects.create_user(username=USER2, email='test@test.com',\
                                              password=PASS2)

        pmg = PmethodGroup.objects.create(name='pmg11', user=self.user1, order=1)
        Pmethod.objects.create(group=pmg, name='pm1', order=1)
        Pmethod.objects.create(group=pmg, name='pm12', order=2)

        pmg = PmethodGroup.objects.create(name='pmg12', user=self.user1, order=2)
        Pmethod.objects.create(group=pmg, name='pm21', order=1)

        #user2
        pmg = PmethodGroup.objects.create(name='pmg21', user=self.user2, order=2)
        Pmethod.objects.create(group=pmg, name='pm211', order=1)
        
        pmg = PmethodGroup.objects.create(name='pmg22', user=self.user2, order=2)
        Pmethod.objects.create(group=pmg, name='pm221', order=1)

        #category
        cg = CategoryGroup.objects.create(name='cg1', order=1)
        Category.objects.create(group=cg, name='c1', order=1)
        Category.objects.create(group=cg, name='c12', order=2)

        cg = CategoryGroup.objects.create(name='cg2', order=2)
        Category.objects.create(group=cg, name='move', id=C_MOVE_ID, order=1)
        Category.objects.create(group=cg, name='withdraw', id=C_WITHDRAW_ID, order=2)


    # monthly report-----------------
    def test_mr_multiuser_ok01(self):
        #user1--
        c = Client()
        c.login(username=USER1, password=PASS1)

        pms = Pmethod.objects.all()
        cs = Category.objects.all()

        self.add_trans2(c, pms, cs)

        
        #user2--
        c = Client()
        c.login(username=USER2, password=PASS2)

        pms = Pmethod.objects.all()
        cs = Category.objects.all()

        response = c.post('/t/add', {'date': '2017/01/01', 'name': '2item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':10000,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 200)



        #actual, alluser--
        response = c.post('/t/monthlyreport',\
                          {\
                           'datefrom': '2017/01', 'dateto': '2017/03',\
                           'alluser':'on'
        })
        self.assertEqual(response.status_code, 200)

        # list method (actual)---
        req = response.wsgi_request
        #self.user1.username=''
        req.user = self.user1
        res = views.monthlyreport(req)
        #print(res)



        #expected--------
        #category
        cgs = CategoryGroup.objects.all()

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

        #monthly report list----
        monthlyreport_list = []

        #2017/01
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 10150
        mr.totalincome = 0
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/1'
        monthlyreport_list.append(mr)
        
        #2017/02
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 3
        mr.totalincome = 10
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/2'
        monthlyreport_list.append(mr)
        
        #2017/03
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 0
        mr.totalincome = 0
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/3'
        monthlyreport_list.append(mr)
        
        

        expected_html = render_to_string('trans/monthlyreport.html',\
                                 {'request.user': USER1,\
                                  'category_list' : cui_list,\
                                  'datefrom' : '2017/01',\
                                  'dateto' : '2017/03',\
                                  'alluser' : True,\
                                  'monthlyreport_list' : monthlyreport_list,\
                                 })

        #print(res.content.decode())
        #print(expected_html)
        
        self.assertEqualExceptCSRF(res.content.decode(), expected_html)



        #--------
        #actual, not alluser--
        c = Client()
        c.login(username=USER1, password=PASS1)
        
        response = c.post('/t/monthlyreport',\
                          {\
                           'datefrom': '2017/01', 'dateto': '2017/03',\
        })
        self.assertEqual(response.status_code, 200)

        # list method (actual)---
        req = response.wsgi_request
        req.user = self.user1
        res = views.monthlyreport(req)
        #print(res)

        #expected--------
        #monthly report list----
        monthlyreport_list = []

        #2017/01
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 150
        mr.totalincome = 0
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/1'
        monthlyreport_list.append(mr)
        
        #2017/02
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 3
        mr.totalincome = 10
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/2'
        monthlyreport_list.append(mr)
        
        #2017/03
        mr = MonthlyreportEachMonthUi()
        mr.totalexpense = 0
        mr.totalincome = 0
        mr.total = mr.totalincome - mr.totalexpense

        mr.yearmonth = '2017/3'
        monthlyreport_list.append(mr)
        
        

        expected_html = render_to_string('trans/monthlyreport.html',\
                                 {'request.user': USER1,\
                                  'category_list' : cui_list,\
                                  'datefrom' : '2017/01',\
                                  'dateto' : '2017/03',\
                                  'monthlyreport_list' : monthlyreport_list,\
                                 })

        #print(res.content.decode())
        #print(expected_html)
        
        self.assertEqualExceptCSRF(res.content.decode(), expected_html)


        




        
        


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


    #add trans------
    def add_trans2(self, c, pms, cs):
        #1st trans---
        response = c.post('/t/add', {'date': '2017/01/01', 'name': 'item1',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':100,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 200)

        #2nd trans---
        response = c.post('/t/add', {'date': '2017/01/31', 'name': 'item2',\
                                     'c':cs[1].id,\
                                     'pm':pms[0].id,\
                                     'expense':50,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 200)
        
        #3rd trans---
        response = c.post('/t/add', {'date': '2017/02/01', 'name': 'item3',\
                                     'c':cs[0].id,\
                                     'pm':pms[1].id,\
                                     'expense':3,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 200)
        
        #4th trans---
        response = c.post('/t/add', {'date': '2017/02/28', 'name': 'item4',\
                                     'c':cs[0].id,\
                                     'pm':pms[0].id,\
                                     'expense':-10,\
                                     'memo':'memo1',\
                                     'share_type':1,\
                                     'user_pay4':'',\
        })
        self.assertEqual(response.status_code, 200)
        
    




        



        
