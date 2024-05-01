import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import json
import codecs

from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template import loader
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
#from django.db import IntegrityError
#from django.db.IntegrityError import ProtectedError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Trans, PmethodGroup, Pmethod, CategoryGroup, Category
from .models import SHARE_TYPES

SHARE_TYPES_OWN = 1
SHARE_TYPES_SHARE = 2
SHARE_TYPES_PAY4OTHER = 3
'''
SHARE_TYPES_OWN_STR = 
SHARE_TYPES_SHARE_STR = 2
SHARE_TYPES_PAY4OTHER_STR = 3
'''

C_MOVE_ID = 101
C_WITHDRAW_ID = 110
#C_WITHDRAW_ID = 103

PM_JACCS_ID = 210


SUICA_KURIKOSHI = '繰\u3000'

JACCS_DISCOUNT = 'discount with J-depo:'

SALARY_MAPPING_FNAME = 'mapping_item_cid.txt'
SALARY_OTHER_ID = 249

CATEGORY_ID_TRANSPORTATION = 3



@login_required(login_url='/login/')
def index(request):
    return indexcore(request, None, None, 2)


def indexcore(request, trans, trans_move, share_type_id):
    latest_trans_list = Trans.objects.filter(user=request.user).order_by('-date', '-id')[:100]

    #pmethod
    #pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')
    pmglist = PmethodGroup.objects.filter(user=request.user).order_by('order')
    pmgroup_list = []
    if 'pmg' in request.POST:
        for pmg in pmglist:
            if pmg.id == int(request.POST['pmg']):
                pmgui = PmethodGroupUi()
                pmgui.id = pmg.id
                pmgui.name = pmg.name
                pmgui.selected = True
                pmgroup_list.append(pmgui)
            else:
                pmgroup_list.append(pmg)
    else:
        pmgroup_list.extend(pmglist)
            

    #sort with group and order---
    pmethod_list = []
    if len(pmgroup_list) > 0:
        if 'pmg' in request.POST:
            pmg = PmethodGroup.objects.get(pk=int(request.POST['pmg']))
        else:
            pmg = pmgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        if 'pm' in request.POST:
            for pm in pmlist:
                if pm.id == int(request.POST['pm']):
                    pmui = PmethodUi()
                    pmui.id = pm.id
                    pmui.name = pm.name
                    pmui.group = pm.group
                    pmui.selected = True
                    pmethod_list.append(pmui)
                else:
                    pmethod_list.append(pm)
        else:
            pmethod_list.extend(pmlist)
                
            
                    
        '''
        pmg = pmgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)
        '''

    pmethod_list_move = pmethod_list


    if trans != None:
        #pmethod_list = []
        #pmethod_list.append(trans.pmethod)
        pmethod_list_move = []
        pmethod_list_move.append(trans_move.pmethod)

    #category---
    cglist = CategoryGroup.objects.order_by('order')
    categorygroup_list = []
    if 'cg' in request.POST:
        for cg in cglist:
            if cg.id == int(request.POST['cg']):
                cgui = CategoryGroupUi()
                cgui.id = cg.id
                cgui.name = cg.name
                cgui.selected = True
                categorygroup_list.append(cgui)
            else:
                categorygroup_list.append(cg)
    else:
        categorygroup_list.extend(cglist)
        

    #sort with group and order---
    category_list = []
    if len(categorygroup_list) > 0:
        #find selected category group
        if 'cg' in request.POST:
            cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
        else:
            cg = categorygroup_list[0]
        clist = Category.objects.filter(group = cg).order_by('order')
        if 'c' in request.POST:
            for c in clist:
                if c.id == int(request.POST['c']):
                    cui = CategoryUi()
                    cui.id = c.id
                    cui.name = c.name
                    cui.group = c.group
                    cui.selected = True
                    category_list.append(cui)
                else:
                    category_list.append(c)
        else:
            category_list.extend(clist)

        
    date = ''
    name = ''
    expense = ''

    if trans != None:
        date = trans.date
        name = trans.name
        expense = trans.expense


    # share_type----
    share_type_list = []
    stui = ShareTypeUi()
    stui.value = 1
    stui.name = 'own'
    if share_type_id == 1:
        stui.selected = True
    share_type_list.append(stui)

    stui = ShareTypeUi()
    stui.value = 2
    stui.name = 'shared'
    if share_type_id == 2:
        stui.selected = True
    share_type_list.append(stui)

    stui = ShareTypeUi()
    stui.value = 3
    stui.name = 'pay4other'
    if share_type_id == 3:
        stui.selected = True
    share_type_list.append(stui)


    context = {'latest_trans_list': latest_trans_list,\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'pmethod_list_move': pmethod_list_move,\
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
               'date' : date,\
               'expense' : expense,\
               'share_type_list' : share_type_list,\
    }
    return render(request, 'trans/index.html', context)
    



# show monthlyrerpot
@login_required(login_url='/login/')
def monthlyreport(request):
    #print (request)

    #date---
    if 'datefrom' not in request.POST:
        dnow = datetime.datetime.now()
        datefrom = dnow + timedelta(weeks=-13)
    else:
        str_datefrom = request.POST['datefrom']
        datefrom = datetime.datetime.strptime(str_datefrom, '%Y/%m')
    str_datefrom = datefrom.strftime('%Y/%m')

    if 'dateto' not in request.POST:
        dnow = datetime.datetime.now()
        dateto = dnow
    else:
        str_dateto = request.POST['dateto']
        dateto = datetime.datetime.strptime(str_dateto, '%Y/%m')
    str_dateto = dateto.strftime('%Y/%m')



    alluser = False
    if 'alluser' in request.POST:
        alluser = True

    #category--
    category_list = get_category_list_ui(request)

    cmove = Category.objects.get(pk=C_MOVE_ID)

    #monthly report---
    monthlyreport_list = []
    for year in range(datefrom.year, dateto.year + 1):
        monthfrom = datefrom.month
        monthto = dateto.month
        if datefrom.year != dateto.year:
            if year != datefrom.year:
                monthfrom = 1
            if year != dateto.year:
                monthto = 12
        for month in range(monthfrom, monthto + 1):
            #mr4months = []
            mr = MonthlyreportEachMonthUi()

            scfrom = datetime.datetime(year, month, 1,0,0,0)
            scto = scfrom + relativedelta(months=1)

            
            # sum total for each month---
            expense = 0
            if alluser:
                expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True).exclude(category=cmove).aggregate(Sum('expense'))
                #expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True).aggregate(Sum('expense'))
                
            else:
                expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True, user=request.user).exclude(category=cmove).aggregate(Sum('expense'))
                

            if expense["expense__sum"] is not None:
                mr.totalexpense = expense["expense__sum"]
            else:
                mr.totalexpense = 0


            if alluser:
                income = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__lt=0, includemonthlysum=True).exclude(category=cmove).aggregate(Sum('expense'))
            else:
                income = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__lt=0, includemonthlysum=True, user=request.user).exclude(category=cmove).aggregate(Sum('expense'))
                
            if income["expense__sum"] is not None:
                mr.totalincome = income["expense__sum"] * -1
            else:
                mr.totalincome = 0

            mr.total = mr.totalincome - mr.totalexpense

            

            #
            eachCates = []
            for c in get_category_list():
                if str(c.id) in request.POST.getlist('categorys'):
                    
                    if alluser:
                        sum = Trans.objects.filter(category=c, date__gte=scfrom, date__lt=scto).aggregate(Sum('expense'))
                    else:
                        sum = Trans.objects.filter(category=c, date__gte=scfrom, date__lt=scto, user=request.user).aggregate(Sum('expense'))
                        

                    eachCate = {}
                    eachCate["category_id"] = c.id
                
                    if sum["expense__sum"] is not None:
                        eachCate["sum"]  = sum["expense__sum"]
                    else:
                        eachCate["sum"]  = 0
                    eachCates.append(eachCate)

            mr.yearmonth = str(year) + "/" + str(month)
            mr.dateTo = str(year) + "/" + str(month) + "/" + get_lastday(year, month)
            mr.eachCates = eachCates
                
            monthlyreport_list.append(mr)

    context = {
        "datefrom":str_datefrom,
        "dateto":str_dateto,
        "category_list":category_list,
        "monthlyreport_list":monthlyreport_list,
        "alluser":alluser,

    }
    return render(request, 'trans/monthlyreport.html', context)


# show advanced UI
@login_required(login_url='/login/')
def advanced(request):

    context = {
    }
    return render(request, 'trans/advanced.html', context)




def add(request):
    date = datetime.datetime.strptime(request.POST['date'], '%Y/%m/%d')

    cid = int(request.POST['c'])
    pmid = int(request.POST['pm'])
    c = Category.objects.get(pk=cid)
    pm = Pmethod.objects.get(pk=pmid)

    expense = int(request.POST['expense'])

    struser_pay4 = request.POST['user_pay4']
    user_pay4 = None
    if struser_pay4 != '':
        user_pay4s = User.objects.filter(username=struser_pay4)[:1]
        # no user
        if len(user_pay4s) == 0:
            context = {'error_message': 'No user for pay for: ' + struser_pay4}
            return render(request, 'trans/message.html', context)
        else:
            user_pay4 = user_pay4s[0]
            

    trans = Trans(date=date, \
                  name=request.POST['name'], \
                  expense=expense, \
                  memo=request.POST['memo'], \
                  category=c,\
                  pmethod=pm,\
                  user=request.user, \
                  share_type=request.POST['share_type'],\
                  user_pay4=user_pay4,\
    )
    trans.save()

    update_balance(trans)

    trans0 = trans


    #for move---
    if cid == C_MOVE_ID:
            pmid2 = int(request.POST['pm2'])
            pm2 = Pmethod.objects.get(pk=pmid2)

            trans = Trans(date=date, \
                          name=request.POST['name'], \
                          expense=expense * -1, \
                          memo=request.POST['memo'], \
                          category=c,\
                          pmethod=pm2,\
                          user=request.user, \
                          share_type=request.POST['share_type'],\
                          user_pay4=user_pay4,\
            )
            trans.save()
            update_balance(trans)
            
    #return redirect('/t/')
    return indexcore(request, trans0, trans, int(request.POST['share_type']))

# dispatch delete, withdraw function
def multi_trans_select(request):
    if 'delete' in request.POST:
        return delete(request)
    elif 'withdraw' in request.POST:
        return withdraw(request)



# delete selected multiple transs
# input: tids
def delete(request):
    #print (request.POST.getlist('tids'))

    #find oldest trans--
    date = None
    oldesttrans = None
    for tid in request.POST.getlist('tids'):
        t = Trans.objects.get(pk=tid)

        if date == None or t.date < date:
            date = t.date
            oldesttrans = t

    try:
        for tid in request.POST.getlist('tids'):
            Trans.objects.get(pk=tid).delete()

        update_balance_para(oldesttrans.pmethod, oldesttrans.user, oldesttrans.date)
        
    except ProtectedError:
        context = {'error_message': 'Failed to delete.'}
        return render(request, 'trans/message.html', context)

    
    return redirect('/t/')

# input: tids
def withdraw(request):
    date = datetime.datetime.strptime(request.POST['date'], '%Y/%m/%d')
    pmid = int(request.POST['pm'])
    c = Category.objects.get(pk=C_WITHDRAW_ID)
    pm = Pmethod.objects.get(pk=pmid)

    try:
        #check not to be already clearanced
        transs = []
        for tid in request.POST.getlist('tids'):
            trans = Trans.objects.get(pk=tid)
            if not trans.includebalance :
                context = {'error_message': str(trans.id) + ' is already cleared.'}
                return render(request, 'trans/message.html', context)
                
            transs.append(trans)

        sum = 0
        for trans in transs:
            trans.includebalance = False
            trans.save()
            update_balance(trans)

            sum += trans.expense

        #added withdrew trans
        trans = Trans(date=date, \
                  name='withdraw', \
                  expense=sum, \
                  memo=request.POST['memo'], \
                  category=c,\
                  pmethod=pm,\
                  user=request.user, \
                  share_type=SHARE_TYPES_OWN,\
                  user_pay4=None,\
                      includemonthlysum=False,\
        )
        trans.save()
        update_balance(trans)

        
    except ProtectedError:
        context = {'error_message': 'Failed to withdraw.'}
        return render(request, 'trans/message.html', context)

    
    return redirect('/t/')


@login_required(login_url='/login/')
def list(request):
    #print(request.user)
    #print(request.POST)
    
    if 'datefrom' not in request.POST:
        str_datefrom = '2017/01/01'
        #datefrom = datetime.datetime.strptime('2000/01/01', '%Y/%m/%d')
    else:
        str_datefrom = request.POST['datefrom']
        #datefrom = datetime.datetime.strptime(request.POST['datefrom'], '%Y/%m/%d')

    datefrom = datetime.datetime.strptime(str_datefrom, '%Y/%m/%d')


    if 'dateto' not in request.POST:
        dateto = datetime.datetime.now()
        str_dateto = dateto.strftime('%Y/%m/%d')
    else:
        str_dateto = request.POST['dateto']
        if str_dateto == '':
            dateto = datetime.datetime.now()
        else:
            dateto = datetime.datetime.strptime(str_dateto, '%Y/%m/%d')
    dateto = dateto + timedelta(days=1)


    #category--
    #print(request.POST.getlist('categorys'))
    latest_trans_list = Trans.objects.filter(user=request.user)\
                        .filter(date__gte=datefrom)\
                        .filter(date__lt=dateto)
                        #.order_by('-date', '-id')[:100]
                        #.order_by('-date', '-id')[:100]

    # for transition from monthly report (no pmehtods)
    pmethods = []
    if 'pmethods' in request.POST:
        pmethods = request.POST.getlist('pmethods')
    else:
        pmethodall = Pmethod.objects.all()
        for pm in pmethodall:
            pmethods.append(str(pm.id))

    if 'filtered' in request.POST:
        categoryall = Category.objects.all()
        for cate in categoryall:
            if not str(cate.id) in request.POST.getlist('categorys'):
                latest_trans_list = latest_trans_list.exclude(category=cate)

        pmethodall = Pmethod.objects.all()
        for pm in pmethodall:
            if not str(pm.id) in pmethods:
            #if not str(pm.id) in request.POST.getlist('pmethods'):
                latest_trans_list = latest_trans_list.exclude(pmethod=pm)


    # filter with includebalance
    includebalance=False
    if request.method != 'GET':
        if 'includebalance' in request.POST:
            includebalance=True
            
            latest_trans_list = latest_trans_list.filter(includebalance=True)


            
    latest_trans_list = latest_trans_list.order_by('-date', '-id')[:500]
    #latest_trans_list = latest_trans_list.order_by('-date', '-id')[:100]

                

    
    #pmethod--
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')
    #sort with group and order---
    pmethod_list = get_pmethod_list_ui(request, pmethods)
    

    #category---
    categorygroup_list = CategoryGroup.objects.order_by('order')
    category_list = get_category_list_ui(request)


    #for diff with actual balance--
    if 'actual' in request.POST and request.POST['actual'] != '':
    #if request.POST['actual'] != '':
        tlist = []

        #actual = request.POST['actual']
        actual = int(request.POST['actual'])
        
        for t in latest_trans_list:
            tui = TransUi()
            tui.id = t.id
            tui.date = t.date
            tui.name = t.name
            tui.expense = t.expense
            tui.balance = t.balance
            tui.diff = actual - t.balance
            
            tui.memo = t.memo
            tui.pmethod = t.pmethod
            tui.category = t.category
            tui.user = t.user
            tui.share_type = t.share_type
            for stype in SHARE_TYPES:
                if stype[0] == t.share_type:
                    #print(stype[1])
                    tui.share_type_str = stype[1]
            
            tui.user_pay4 = t.user_pay4
            tui.includebalance = t.includebalance
            tui.includemonthlysum = t.includemonthlysum

            tlist.append(tui)

        latest_trans_list = []
        latest_trans_list.extend(tlist)
    else:
        actual = 0
            
        
    #--
    #paginator = Paginator(latest_trans_list, 10)
    paginator = Paginator(latest_trans_list, 100)

    page = request.GET.get('page')
    #print(page)
    try:
        transs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        transs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        transs = paginator.page(paginator.num_pages)


    if request.method == 'GET':
        detail = False
    else:
        if 'detail' in request.POST:
            detail = True
        else:
            detail = False

        
    context = {'latest_trans_list': transs,\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
               'datefrom' : str_datefrom,\
               'dateto' : str_dateto,\
               'actual' : actual,\
               'detail' : detail,\
               'includebalance' : includebalance,\
    }
    return render(request, 'trans/list.html', context)


# return json
def sum_expense(request):
    #print(request.GET)
    #print(request.GET.getlist('ids[]'))

    sum = 0
    for tid in request.GET.getlist('ids[]'):
        trans = Trans.objects.get(pk=tid)
        #print (trans.expense)
        sum += trans.expense

    context = {'sum' : sum}

    jsonstring = json.dumps(context)
    return HttpResponse(jsonstring)




#--- suica ----

def suica_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)


    pmethodgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')

    pmethod_list = []
    if len(pmethodgroup_list) > 0:
        pmg = pmethodgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)
    
    date = datetime.datetime.now()
    year = date.year


    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,\
                   'category_list' : category_list,\
                   'pmethodgroup_list': pmethodgroup_list,\
                   'pmethod_list': pmethod_list,\
                   'year': year,\
        }
        return render(request, 'trans/suica_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,\
                       'category_list' : category_list,\
                       'pmethodgroup_list': pmethodgroup_list,\
                       'pmethod_list': pmethod_list,\
                       'year': year,\
                       'error_message': 'File is mandatory.',\
            }
            return render(request, 'trans/suica_upload.html', context)
            
        f = request.FILES['file']

        with open('tmp_suica.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        f = open('tmp_suica.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        pmid = int(request.POST['pm'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=pmid)

        c_transportation = Category.objects.get(pk=CATEGORY_ID_TRANSPORTATION)

        trans_list = []
        tmpid = 1
        for l in contents:
            splts = l.split('\t')
            trans = TransUi()
            #trans = Trans()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1

            strdate = request.POST['year'] + '/' + splts[1]
            strdate = strdate.strip()

            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            trans.name = splts[2] + splts[3]  + splts[4]  + splts[5]
            #trans.name = splts[1] + splts[4]  + splts[3]  + splts[4]
            """
            if len(splts) == 7:
                if splts[6].count('-'):
                    expense = splts[6].replace('-', '').replace(',', '')
                else:
                    expense = splts[6].replace('+', '-').replace(',', '')
                    #expense = '-' + expense
                #expense = splts[5].replace('¥', '').replace(',', '')
                trans.expense = expense
            """                
            expense = splts[7].replace('\n', '').replace(',', '').replace('+', '')

            if len(expense) != 0:
                trans.expense = int(expense)
            else:
                continue

            str0 = splts[2].strip()
            if str0 in ["入", "ﾊﾞｽ等"]:
                trans.category = c_transportation
            else:
                trans.category = c

            #print(splts[2])
            #print(trans.category.name)


            trans.pmethod = pm

            #check same trans
            checktranslist = Trans.objects.filter(date=trans.date, expense=trans.expense, category=trans.category, pmethod=pm)
            #checktranslist = Trans.objects.filter(date=trans.date, expense=trans.expense, category=c, pmethod=pm)

            if len(checktranslist) > 0:
                trans.selected = False

            if trans.name != SUICA_KURIKOSHI:
                trans_list.append(trans)
        

        context = {'categorygroup_list': categorygroup_list,\
                   'pmethodgroup_list': pmethodgroup_list,\
                   'trans_list': trans_list,\
                   }
        return render(request, 'trans/suica_check.html', context)
        
        

def suica_check(request):
    suica_jaccs_register(request)
    """
    # checked trans
    tids = request.POST.getlist('tids')
    dates = request.POST.getlist('dates')
    cs = request.POST.getlist('cs')
    names = request.POST.getlist('names')
    expenses = request.POST.getlist('expenses')
    pmethods = request.POST.getlist('pmethods')
    memos = request.POST.getlist('memos')
    share_types = request.POST.getlist('share_types')

    i = 1
    for expense in expenses:
        if str(i) in tids:
            date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')
            c = Category.objects.get(pk=cs[i-1])
            pm = Pmethod.objects.get(pk=pmethods[i-1])

            trans = Trans(date=date, \
                          name=names[i-1], \
                          expense=expenses[i-1], \
                          memo=memos[i-1], \
                          category=c,\
                          pmethod=pm,\
                          user=request.user, \
                          share_type=share_types[i-1],\
            )
            trans.save()

        i += 1
    update_balance(trans)
    """

    return redirect('/t/')




    
"""
def handle_uploaded_suica(f):
    with open('suica/tmp.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
"""



#--- jaccs ----

def jaccs_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)


    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,\
                   'category_list' : category_list,\
        }
        return render(request, 'trans/jaccs_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,\
                       'category_list' : category_list,\
                       'error_message': 'File is mandatory.',\
            }
            return render(request, 'trans/jaccs_upload.html', context)
            

        '''
        f = request.FILES['file']

        with open('tmp_jaccs.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        '''

        '''
        content = f.read().decode('utf-8')
        fout = open('tmp_jaccs.txt', 'w')
        fout.write(content)
        '''

        
        f = codecs.EncodedFile(request.FILES['file'],"utf-8")
        content = f.read()
        #content = f.read()
        #print(content)
        #print(content.decode('utf-8'))

        fout = open('tmp_jaccs.txt', 'w')
        fout.write(content.decode('utf-8'))
        fout.close()
        

        
        '''
        f = codecs.open('tmp_jaccs.txt', 'r', 'ascii')
        content = f.read().decode('utf-8')
        print(content)
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()
        '''

        f = open('tmp_jaccs.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_JACCS_ID)

        trans_list = []
        tmpid = 1
        for l in contents:
            splts = l.split('\t')

            #print('------')
            #print(splts)

            if len(splts) == 1:
                continue

            if splts[1] == '':
                continue

            
            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            strdate = '20' + splts[1]
            #strdate = request.POST['year'] + '/' + splts[0]
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            trans.name = splts[2] + splts[3]

            expense = splts[10].replace(',', '')
            trans.expense = expense

            price = splts[8].replace(',', '')
            if expense != price:
                trans.memo = JACCS_DISCOUNT + price

            trans.category = c
            trans.pmethod = pm

            trans.share_type = SHARE_TYPES_SHARE
            
            #check same trans--
            checktranslist = Trans.objects.filter(date=trans.date, expense=trans.expense, pmethod=pm)
            #checktranslist = Trans.objects.filter(date=trans.date, expense=trans.expense, category=c, pmethod=pm)            
            if len(checktranslist) > 0:
                trans.selected = False

            #tmp for migrated data
            datetmp = trans.date + timedelta(days=-1)
            checktranslist = Trans.objects.filter(date__gte=datetmp)\
                             .filter(date__lte=trans.date)\
                             .filter(expense=trans.expense, pmethod=pm)
            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        """
        category_list = []
        if len(categorygroup_list) > 0:
            cg = categorygroup_list[0]
            clist = Category.objects.filter(group = cg).order_by('order')
            category_list.extend(clist)
        """
        category_list = []
        if len(categorygroup_list) > 0:
            #find selected category group
            if 'cg' in request.POST:
                cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
            else:
                cg = categorygroup_list[0]
            clist = Category.objects.filter(group = cg).order_by('order')
            if 'c' in request.POST:
                for c in clist:
                    if c.id == int(request.POST['c']):
                        cui = CategoryUi()
                        cui.id = c.id
                        cui.name = c.name
                        cui.group = c.group
                        cui.selected = True
                        category_list.append(cui)
                    else:
                        category_list.append(c)
            else:
                category_list.extend(clist)
        
            

        context = {'categorygroup_list': categorygroup_list,\
                   'category_list': category_list,\
                   'trans_list': trans_list,\
                   }
        return render(request, 'trans/jaccs_check.html', context)
        
        

def jaccs_check(request):
    suica_jaccs_register(request)

    return redirect('/t/')

def suica_jaccs_register(request):
    # checked trans
    tids = request.POST.getlist('tids')
    dates = request.POST.getlist('dates')
    cs = request.POST.getlist('cs')
    names = request.POST.getlist('names')
    expenses = request.POST.getlist('expenses')
    pmethods = request.POST.getlist('pmethods')
    memos = request.POST.getlist('memos')
    share_types = request.POST.getlist('share_types')

    i = 1
    for expense in expenses:
        if str(i) in tids:
            date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')
            c = Category.objects.get(pk=cs[i-1])
            pm = Pmethod.objects.get(pk=pmethods[i-1])

            trans = Trans(date=date, \
                          name=names[i-1], \
                          expense=expenses[i-1], \
                          memo=memos[i-1], \
                          category=c,\
                          pmethod=pm,\
                          user=request.user, \
                          share_type=share_types[i-1],\
            )
            trans.save()

        i += 1
    update_balance(trans)
    




    
"""

def handle_uploaded_jaccs(f):
    with open('jaccs/tmp.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
"""


#--- salary ----

def salary_upload(request):
    pmethodgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')

    pmethod_list = []
    if len(pmethodgroup_list) > 0:
        pmg = pmethodgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)

    if request.method == 'GET':
        context = {'pmethodgroup_list': pmethodgroup_list,\
                   'pmethod_list': pmethod_list,\
        }
        return render(request, 'trans/salary_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {\
                       'pmethodgroup_list': pmethodgroup_list,\
                       'pmethod_list': pmethod_list,\
                       'error_message': 'File is mandatory.',\
            }
            return render(request, 'trans/salary_upload.html', context)

        if request.POST['date'] == '':
            context = {\
                       'pmethodgroup_list': pmethodgroup_list,\
                       'pmethod_list': pmethod_list,\
                       'error_message': 'Date should be YY/mm/dd.' + request.POST['date'],\
            }
            return render(request, 'trans/salary_upload.html', context)


        
        f = request.FILES['file']

        with open('tmp_salary.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        f = open('tmp_salary.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()


        #open mapping between item and cid--
        f = open(SALARY_MAPPING_FNAME, 'r')
        CS_SALARY = {}
        for l in f.readlines():
            splts = l.split(',')
            CS_SALARY[splts[0]] = int(splts[1])
        f.close()


        # get default pmethod
        pmid = int(request.POST['pm'])
        pm = Pmethod.objects.get(pk=pmid)

        trans_list = []
        tmpid = 1
        fIncome = True
        for l in contents:
            if 'in\n' == l:
                fIncome = True
                continue
            elif 'out\n' == l:
                fIncome = False
                continue
                
            splts = l.split(' : ')
            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            strdate = request.POST['date']
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            
            trans.name = ''
            expense = splts[1].replace(',', '').replace('\n','')
            expense = expense.replace('−', '-')
            if fIncome:
                if not expense.count('-'):
                    expense = '-' + expense
                else:
                    expense = expense.replace('-', '') 

            trans.expense = expense
            trans.pmethod = pm

            trans.name = splts[0]


            #category
            if not splts[0] in CS_SALARY:
                #continue
                cid = SALARY_OTHER_ID
            else:
                cid = CS_SALARY[splts[0]]
            c = Category.objects.get(pk=cid)
            trans.category = c

            #check same trans
            checktranslist = Trans.objects.filter(date=trans.date, expense=trans.expense, category=c, pmethod=pm)

            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        context = {
                   'trans_list': trans_list,\
                   }
        return render(request, 'trans/salary_check.html', context)
        
        

def salary_check(request):
    suica_jaccs_register(request)

    return redirect('/t/')



            
#--everymonth-----
def everymonth(request):
    #pmethod
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')

    #sort with group and order---
    pmethod_list = []
    if len(pmgroup_list) > 0:
        pmg = pmgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)


    #category---
    categorygroup_list = CategoryGroup.objects.order_by('order')

    #sort with group and order---
    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)


    str_datefrom = ''
    str_dateto = ''

    # update period--------
    date_list = []
    if 'update' in request.POST:
        #action_update = request.POST['update']
        
        str_datefrom = request.POST['datefrom']
        datefrom = datetime.datetime.strptime(str_datefrom, '%Y/%m')

        str_dateto = request.POST['dateto']
        dateto = datetime.datetime.strptime(str_dateto, '%Y/%m')

        for year in range(datefrom.year, dateto.year + 1):
            monthfrom = datefrom.month
            monthto = dateto.month
            if datefrom.year != dateto.year:
                if year != datefrom.year:
                    monthfrom = 1
                if year != dateto.year:
                    monthto = 12
            for month in range(monthfrom, monthto + 1):
                date = datetime.datetime(year, month, 1,0,0,0)
                date_list.append(date)
        


    #register
    if 'register' in request.POST:
        dates = request.POST.getlist('dates')
        names = request.POST.getlist('names')
        expenses = request.POST.getlist('expenses')
        memos = request.POST.getlist('memos')

        cid = int(request.POST['c'])
        pmid = int(request.POST['pm'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=pmid)

        share_type=request.POST['share_type']
            

        i = 1
        for expense in expenses:
            if expense != '0':
                date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')

                trans = Trans(date=date, \
                              name=names[i-1], \
                              expense=expenses[i-1], \
                              memo=memos[i-1], \
                              category=c,\
                              pmethod=pm,\
                              user=request.user, \
                              share_type=share_type,\
                )
                trans.save()

            i += 1
        update_balance(trans)

    context = {\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
               'date_list' : date_list,\
               "datefrom":str_datefrom,\
               "dateto":str_dateto,\
    }
    return render(request, 'trans/everymonth.html', context)



# show annualrerpot----
@login_required(login_url='/login/')
def annualreport(request):
    #print (request)

    #year---
    if 'yearfrom' not in request.POST:
        dnow = datetime.datetime.now()
        yearnow = dnow.year
        yearfrom = yearnow - 5
    else:
        yearfrom = request.POST['yearfrom']

    if 'dateto' not in request.POST:
        dnow = datetime.datetime.now()
        yearnow = dnow.year
        yearto = yearnow
    else:
        yearto = request.POST['dateto']

    alluser = False
    if 'alluser' in request.POST:
        alluser = True

    #category--
    category_list = get_category_list_ui(request)

    cmove = Category.objects.get(pk=C_MOVE_ID)

    #annual report---
    annualreport_list = []
    for year in range(int(yearfrom), int(yearto) + 1):
        mr = MonthlyreportEachMonthUi()

        scfrom = datetime.datetime(year, 1, 1,0,0,0)
        scto = scfrom + relativedelta(years=1)
            
        # sum total for each month---
        expense = 0
        if alluser:
            expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True).exclude(category=cmove).aggregate(Sum('expense'))
        else:
            expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True, user=request.user).exclude(category=cmove).aggregate(Sum('expense'))
                

        if expense["expense__sum"] is not None:
            mr.totalexpense = expense["expense__sum"]
        else:
            mr.totalexpense = 0


        if alluser:
            income = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__lt=0, includemonthlysum=True).exclude(category=cmove).aggregate(Sum('expense'))
        else:
            income = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__lt=0, includemonthlysum=True, user=request.user).exclude(category=cmove).aggregate(Sum('expense'))
                
        if income["expense__sum"] is not None:
            mr.totalincome = income["expense__sum"] * -1
        else:
            mr.totalincome = 0

        mr.total = mr.totalincome - mr.totalexpense

            

        #
        eachCates = []
        for c in get_category_list():
            if str(c.id) in request.POST.getlist('categorys'):
                    
                if alluser:
                    sum = Trans.objects.filter(category=c, date__gte=scfrom, date__lt=scto).aggregate(Sum('expense'))
                else:
                    sum = Trans.objects.filter(category=c, date__gte=scfrom, date__lt=scto, user=request.user).aggregate(Sum('expense'))
                        

                eachCate = {}
                eachCate["category_id"] = c.id
                
                if sum["expense__sum"] is not None:
                    eachCate["sum"]  = sum["expense__sum"]
                else:
                    eachCate["sum"]  = 0
                eachCates.append(eachCate)

        mr.yearmonth = str(year)
        mr.dateTo = str(year) + "/" + str(12) + "/" + get_lastday(year, 12)
        mr.eachCates = eachCates
                
        annualreport_list.append(mr)

    context = {
        "yearfrom":yearfrom,
        "yearto":yearto,
        "category_list":category_list,
        "annualreport_list":annualreport_list,
        "alluser":alluser,
    }
    return render(request, 'trans/annualreport.html', context)



# show totalbalance-----
@login_required(login_url='/login/')
def totalbalance(request):
    #pmethod
    pmgroup_list = PmethodGroup.objects.order_by('order')


    sum = 0

    balance_list = []
    for pmg in pmgroup_list:
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')

        for pm in pmlist:
            trans = Trans.objects.filter(pmethod = pm).order_by('-date')[:1]
                    
            b = BalanceUi()
            b.pmgroup = pmg.name
            b.pmethod = pm.name
            b.user = pmg.user
            if len(trans) > 0:
                b.balance = trans[0].balance
                b.lastupdated = trans[0].date
                sum += trans[0].balance
            else:
                b.balance = 0
                b.lastupdated = ''

            balance_list.append(b)
            
    context = {
        "balance_list":balance_list,
        "sum": sum,
    }
    return render(request, 'trans/totalbalance.html', context)


# show shared expense-----
@login_required(login_url='/login/')
def sharedexpense(request):

    users = User.objects.order_by('id')

    sharedexpense_list = []
    for user in users:
        se = SharedexpenseUi()
        se.user = user

        se.shared = Trans.objects.filter(user=user, share_type=SHARE_TYPES_SHARE).aggregate(Sum('expense'))['expense__sum']
        if se.shared == None:
            se.shared = 0

        se.pay4other = Trans.objects.filter(user=user, share_type=SHARE_TYPES_PAY4OTHER).aggregate(Sum('expense'))['expense__sum']
        if se.pay4other == None:
            se.pay4other = 0

        se.total = se.shared / 2 + se.pay4other

        sharedexpense_list.append(se)
        
            
    context = {
        'sharedexpense_list': sharedexpense_list,
    }
    return render(request, 'trans/sharedexpense.html', context)


class SharedexpenseUi():
    user = None
    shared = 0
    pay4other = 0

    total = 0
    






#---methods for internal------------------------
        
def get_pmethod_list_ui(request, pmethods):
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')
    pmethod_list = []
    """
    for pmg in pmgroup_list:
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)
    """
    for pmg in pmgroup_list:
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')

        first = True
        for pm in pmlist:
            pmui = PmethodUi()
            pmui.id = pm.id
            pmui.name = pm.name
            pmui.group = pm.group
            pmui.first_in_group = first
            first = False
            if 'filtered' in request.POST:
                if str(pm.id) in pmethods:
                #if str(pm.id) in request.POST.getlist('pmethods'):
                    pmui.selected = True
                else:
                    pmui.selected = False
            else:
                pmui.selected = True
            pmethod_list.append(pmui)
    
    return pmethod_list

def get_category_list():
    categorygroup_list = CategoryGroup.objects.order_by('order')

    #sort with group and order---
    category_list = []
    for cg in categorygroup_list:
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)
    
    return category_list

def get_category_list_ui(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    #sort with group and order---
    category_list = []
    #checkbox value
    #categorys = []
    for cg in categorygroup_list:
        clist = Category.objects.filter(group = cg).order_by('order')
        #category_list.extend(clist)

        #for list filter. first item in each group
        first = True
        for c in clist:
            cui = CategoryUi()
            cui.id = c.id
            cui.name = c.name
            cui.group = c.group
            cui.first_in_group = first
            first = False
            if 'filtered' in request.POST:
                if str(c.id) in request.POST.getlist('categorys'):
                    cui.selected = True
                else:
                    #TODO how to unchecked checkbox..
                    cui.selected = False
            else:
                cui.selected = True
            category_list.append(cui)

    return category_list
    


def get_lastday(year, month):
    ym = datetime.datetime(year, month, 1, 0, 0, 0)
    ym += relativedelta(months=1)
    ym += relativedelta(days=-1)

    return str(ym.day)




class TransUi(Trans):
    selected = True

    #for list
    diff = 0
    str_share_type = ''

class CategoryGroupUi(CategoryGroup):
    selected = False

class CategoryUi(Category):
    selected = False
    first_in_group = False

    
class PmethodGroupUi(PmethodGroup):
    selected = False

class PmethodUi(Pmethod):
    selected = False
    first_in_group = False

class MonthlyreportEachMonthUi():
    # list of dictionary
    #sum, cateid for each categories
    eachCates = []

    # for display
    yearmonth = "yyyy/mm"
    # for transition to list view
    dateTo = "yyyy/mm/dd"

    totalexpense = 0
    totalincome = 0
    total = 0

class BalanceUi():
    pmgroup = ''
    pmethod = ''
    user = ''
    balance = 0
    lastupdated = ''

class ShareTypeUi():
    value = ''
    name = ''
    selected = False
    


    
    



#---
#input: added trans
def update_balance(trans):
    update_balance_para(trans.pmethod, trans.user, trans.date)

#input: added trans
def update_balance_para(pmethod, user, date):
    # update balance---
    prevTrans = Trans.objects.filter(pmethod=pmethod, user=user, date__lt=date).order_by('-date', '-id')[:1]

    prevBalance = 0
    if len(prevTrans) != 0:
        prevBalance = prevTrans[0].balance

    #print("------" + str(prevBalance))

    # get newer transs--
    transs = Trans.objects.filter(pmethod=pmethod, user=user, date__gte=date).order_by('date', 'id')

    for t in transs:
        #print(t.name)
        if t.includebalance :
            t.balance = prevBalance - t.expense
        else:
            t.balance = prevBalance
        t.save()
        prevBalance = t.balance
        




# pmethod-----------------------
def index_pmethod(request):
    #pmethod_list = Pmethod.objects.order_by('-group')
    #pmethod_list = Pmethod.objects.order_by('-order')[:30]
    #pmgroup_list = PmethodGroup.objects.order_by('order')
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')

    #sort with group and order---
    pmethod_list = []
    for pmg in pmgroup_list:
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)


    #category---
    categorygroup_list = CategoryGroup.objects.order_by('order')

    #sort with group and order---
    category_list = []
    for cg in categorygroup_list:
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)

    context = {'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,}
    #context['error_message'] = error
    return render(request, 'trans/index_pmethod.html', context)


def add_pmethod(request):
    pmg = PmethodGroup.objects.get(pk=request.POST['pmg'])
    pmethod = Pmethod(name=request.POST['name'], group=pmg)
    pmethod.save()

    pmethod.order = pmethod.id
    pmethod.save()

    #TODO
    return redirect('/t/pmethod')
    
def edit_pmethod(request, pmethod_id):
    pm = Pmethod.objects.get(pk=pmethod_id)

    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('-order')[:30]

    context = {'pm': pm, 'pmgroup_list': pmgroup_list}
    return render(request, 'trans/edit_pmethod.html', context)

def update_pmethod(request, pmethod_id):
    pmg = PmethodGroup.objects.get(pk=pmethod_id)

    pmg.name = request.POST['name']
    pmg.save()

    return redirect('/t/pmethod')


def delete_pmethod(request, pmethod_id):
    try:
        Pmethod.objects.get(pk=pmethod_id).delete()
    except ProtectedError:
        print ('todo')

    return redirect('/t/pmethod')

def up_pmethod(request, pmethod_id):
    pm = Pmethod.objects.get(pk=pmethod_id)

    pms = Pmethod.objects.filter(group = pm.group).order_by('-order')

    #find uppper pm
    fTargetNext = False
    target = None
    for p in pms:
        if fTargetNext:
            target = p
            break
        if pm.id == p.id:
            fTargetNext = True
            
    if target != None:
        lowerOrder = pm.order
        pm.order = target.order
        pm.save()

        target.order = lowerOrder
        target.save()

    return redirect('/t/pmethod')




#pmgroup------------------------------
def add_pmgroup(request):
    pgmethod = PmethodGroup(name=request.POST['name'],
                            user=request.user,
    )
    pgmethod.save()

    pgmethod.order = pgmethod.id
    pgmethod.save()

    #TODO
    return redirect('/t/pmethod')
    
def edit_pmgroup(request, pmgroup_id):
    pmg = PmethodGroup.objects.get(pk=pmgroup_id)

    context = {'pmg': pmg}
    return render(request, 'trans/edit_pmgroup.html', context)

def update_pmgroup(request, pmgroup_id):
    pmg = PmethodGroup.objects.get(pk=pmgroup_id)

    pmg.name = request.POST['name']
    pmg.save()

    return redirect('/t/pmethod')


def delete_pmgroup(request, pmgroup_id):
    try:
        PmethodGroup.objects.get(pk=pmgroup_id).delete()
    except ProtectedError:
        context = {'error_message': 'Failed to delete, because the payment method group has some related methods.'}
        return render(request, 'trans/message.html', context)

        #return HttpResponse("Failed to delete, because the payment method group has some related methods.")

    return redirect('/t/pmethod')


def up_pmgroup(request, pmgroup_id):
    pmg = PmethodGroup.objects.get(pk=pmgroup_id)

    pmgs = PmethodGroup.objects.filter(user=request.user).order_by('-order')

    #find uppper pmg
    fTargetNext = False
    target = None
    for p in pmgs:
        if fTargetNext:
            target = p
            break
        if pmg.id == p.id:
            fTargetNext = True
            
    if target != None:
        lowerOrder = pmg.order
        pmg.order = target.order
        pmg.save()

        target.order = lowerOrder
        target.save()

    return redirect('/t/pmethod')


# return json
def list_pmgroup(request, pmgroup_id):

    #pm---
    pmg = PmethodGroup.objects.get(pk=pmgroup_id)

    clist = Pmethod.objects.filter(group = pmg).order_by('order')

    clistdic = []
    for c in clist:
        dic = {}
        dic['id'] = c.id
        dic['name'] = c.name
        clistdic.append(dic)
    
    context = {'pmethod_list' : clistdic}

    jsonstring = json.dumps(context)
    return HttpResponse(jsonstring)





#category----
def add_category(request):
    cg = CategoryGroup.objects.get(pk=request.POST['cg'])
    category = Category(name=request.POST['name'], group=cg)
    category.save()

    category.order = category.id
    category.save()

    
    #TODO
    return redirect('/t/pmethod')

#move to edit view
def edit_category(request, category_id):
    c = Category.objects.get(pk=category_id)

    cgroup_list = CategoryGroup.objects.order_by('-order')[:30]

    context = {'c': c, 'cgroup_list': cgroup_list}
    return render(request, 'trans/edit_category.html', context)

def update_category(request, category_id):
    cg = CategoryGroup.objects.get(pk=category_id)

    cg.name = request.POST['name']
    cg.save()

    return redirect('/t/pmethod')


def delete_category(request, category_id):
    try:
        Category.objects.get(pk=category_id).delete()
    except ProtectedError:
        print ('todo')

    return redirect('/t/pmethod')

def up_category(request, category_id):
    pm = Category.objects.get(pk=category_id)

    pms = Category.objects.filter(group = pm.group).order_by('-order')

    #find uppper pm
    fTargetNext = False
    target = None
    for p in pms:
        if fTargetNext:
            target = p
            break
        if pm.id == p.id:
            fTargetNext = True
            
    if target != None:
        lowerOrder = pm.order
        pm.order = target.order
        pm.save()

        target.order = lowerOrder
        target.save()

    return redirect('/t/pmethod')






#category group------------------------------
def add_categorygroup(request):
    categorygroup = CategoryGroup(name=request.POST['name'])
    categorygroup.save()

    categorygroup.order = categorygroup.id
    categorygroup.save()

    #TODO
    return redirect('/t/pmethod')
    
def edit_categorygroup(request, categorygroup_id):
    cg = CategoryGroup.objects.get(pk=categorygroup_id)

    context = {'cg': cg}
    return render(request, 'trans/edit_categorygroup.html', context)

def update_categorygroup(request, categorygroup_id):
    cg = CategoryGroup.objects.get(pk=categorygroup_id)

    cg.name = request.POST['name']
    cg.save()

    return redirect('/t/pmethod')


def delete_categorygroup(request, categorygroup_id):
    try:
        CategoryGroup.objects.get(pk=categorygroup_id).delete()
    except ProtectedError:
        context = {'error_message': 'Failed to delete, because the category group has some related categories.'}
        return render(request, 'trans/message.html', context)

    return redirect('/t/pmethod')


def up_categorygroup(request, categorygroup_id):
    cg = CategoryGroup.objects.get(pk=categorygroupy_id)

    cgs = CategoryGroup.objects.order_by('-order')

    #find uppper cg
    fTargetNext = False
    target = None
    for p in cgs:
        if fTargetNext:
            target = p
            break
        if cg.id == p.id:
            fTargetNext = True
            
    if target != None:
        lowerOrder = cg.order
        cg.order = target.order
        cg.save()

        target.order = lowerOrder
        target.save()

    return redirect('/t/pmethod')


# return json
def list_categorygroup(request, categorygroup_id):

    #category---
    cg = CategoryGroup.objects.get(pk=categorygroup_id)

    clist = Category.objects.filter(group = cg).order_by('order')

    clistdic = []
    for c in clist:
        dic = {}
        dic['id'] = c.id
        dic['name'] = c.name
        clistdic.append(dic)
    
    context = {'category_list' : clistdic}

    jsonstring = json.dumps(context)
    return HttpResponse(jsonstring)






