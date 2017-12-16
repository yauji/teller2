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
    def test_mr_ok01(self):
        #kokokara
        c = Client()
        c.login(username='test1', password='password')

        pms = Pmethod.objects.all()
        #print(pms)
        cs = Category.objects.all()

        self.add_trans2(c, pms, cs)

        response = c.post('/t/monthlyreport',\
                          {\
                           'datefrom': '2017/01', 'dateto': '2017/03',\
        })
        self.assertEqual(response.status_code, 200)


        # list method (actual)---
        req = response.wsgi_request
        self.user.username=''
        req.user = self.user
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

        #date---
        """
        dateto = datetime.datetime.now()
        str_dateto = dateto.strftime('%Y/%m')
        datefrom = dateto  + timedelta(weeks=-13)
        str_datefrom = datefrom.strftime('%Y/%m')
        """


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
                                 {'request.user': 'admin',\
                                  'category_list' : cui_list,\
                                  'datefrom' : '2017/01',\
                                  'dateto' : '2017/03',\
                                  'alluser' : True,\
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




        



        
