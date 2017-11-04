import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import json

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

SHARE_TYPES_OWN = 1

C_MOVE_ID = 101
C_WITHDRAW_ID = 103

@login_required(login_url='/login/')
def index(request):
    latest_trans_list = Trans.objects.filter(user=request.user).order_by('-date', '-id')[:30]
    #pmethod
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')

    #sort with group and order---
    pmethod_list = []
    if len(pmgroup_list) > 0:
        pmg = pmgroup_list[0]
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)
    """
    for pmg in pmgroup_list:
        pmlist = Pmethod.objects.filter(group = pmg).order_by('order')
        pmethod_list.extend(pmlist)
    """



    #category---
    categorygroup_list = CategoryGroup.objects.order_by('order')

    #sort with group and order---
    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)
    """
    for cg in categorygroup_list:
        clist = Category.objects.filter(group = cg).order_by('order')
        category_list.extend(clist)
    """

    
    context = {'latest_trans_list': latest_trans_list,\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
    }
    return render(request, 'trans/index.html', context)

"""
def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % question_id)

def results(request, question_id):
    #response = "You're looking at the results of question %s."
    #return HttpResponse(response % question_id)
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})

def vote(request, question_id):
    #return HttpResponse("You're voting on question %s." % question_id)
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
"""


# show monthlyrerpot
@login_required(login_url='/login/')
def monthlyreport(request):
    print (request)

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


    #todo
    alluser = True

    #category--
    category_list = get_category_list_ui(request)

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
            expense = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__gte=0, includemonthlysum=True).aggregate(Sum('expense'))

            if expense["expense__sum"] is not None:
                mr.totalexpense = expense["expense__sum"]
            else:
                mr.totalexpense = 0
                
            income = Trans.objects.filter(date__gte=scfrom, date__lt=scto, expense__lt=0, includemonthlysum=True).aggregate(Sum('expense'))
            if income["expense__sum"] is not None:
                mr.totalincome = income["expense__sum"] * -1
            else:
                mr.totalincome = 0

            mr.total = mr.totalincome - mr.totalexpense

            

            #
            eachCates = []
            for c in get_category_list():
                if str(c.id) in request.POST.getlist('categorys'):
                    #todo consider user
                    sum = Trans.objects.filter(category=c, date__gte=scfrom, date__lt=scto).aggregate(Sum('expense'))

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


    return redirect('/t/')

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
        str_datefrom = '2000/01/01'
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


    #category--
    #print(request.POST.getlist('categorys'))
    latest_trans_list = Trans.objects.filter(user=request.user)\
                        .filter(date__gte=datefrom)\
                        .filter(date__lte=dateto)
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

    latest_trans_list = latest_trans_list.order_by('-date', '-id')[:300]
    #latest_trans_list = latest_trans_list.order_by('-date', '-id')[:100]

                

    
    #pmethod--
    pmgroup_list = PmethodGroup.objects.filter(user=request.user).order_by('order')
    #sort with group and order---
    pmethod_list = get_pmethod_list_ui(request, pmethods)
    

    #category---
    categorygroup_list = CategoryGroup.objects.order_by('order')
    category_list = get_category_list_ui(request)

    
    #--
    paginator = Paginator(latest_trans_list, 50)

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

    #print(transs.number)
        
    context = {'latest_trans_list': transs,\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
               'datefrom' : str_datefrom,\
               'dateto' : str_dateto,\
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




"""
@login_required(login_url='/login/')
def move(request):

    context = {
    }
    return render(request, 'trans/move.html', context)
"""

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




class CategoryUi(Category):
    selected = False
    first_in_group = False

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

    
    



#---
#input: added trans
def update_balance(trans):
    update_balance_para(trans.pmethod, trans.user, trans.date)

#input: added trans
def update_balance_para(pmethod, user, date):
    # update balance---
    prevTrans = Trans.objects.filter(pmethod=pmethod, user=user, date__lt=date).order_by('date')[:1]

    prevBalance = 0
    if len(prevTrans) != 0:
        prevBalance = prevTrans[0].balance

    # get newer transs--
    transs = Trans.objects.filter(pmethod=pmethod, user=user, date__gte=date).order_by('date')

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






