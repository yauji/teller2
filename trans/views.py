import datetime
import json

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template import loader
from django.db.models.deletion import ProtectedError
#from django.db import IntegrityError
#from django.db.IntegrityError import ProtectedError
from django.contrib.auth.decorators import login_required


from .models import Trans, PmethodGroup, Pmethod, CategoryGroup, Category

@login_required(login_url='/login/')
def index(request):
    latest_trans_list = Trans.objects.order_by('-date')[:30]
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    #output = ', '.join([q.question_text for q in latest_question_list])
    #return HttpResponse(output)
    """
    template = loader.get_template('polls/index.html')
    context = {
        'latest_question_list': latest_question_list,
    }
    return HttpResponse(template.render(context, request))
    """
    #pmethod
    pmgroup_list = PmethodGroup.objects.order_by('order')

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

    
    context = {'latest_trans_list': latest_trans_list,\
               'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list, \
               'categorygroup_list' : categorygroup_list , \
               'category_list' : category_list,\
    }
    return render(request, 'trans/index.html', context)


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





def add(request):
    #today = datetime.date.today()
    date = datetime.datetime.strptime(request.POST['date'], '%Y/%m/%d')

    cid = int(request.POST['c'])
    pmid = int(request.POST['pm'])
    c = Category.objects.get(pk=cid)
    pm = Pmethod.objects.get(pk=pmid)

    expense = int(request.POST['expense'])

    trans = Trans(date=date, \
                  name=request.POST['name'], \
                  expense=expense, \
                  memo=request.POST['memo'], \
                  category=c,\
                  pmethod=pm,\
                  user=request.user, \
    )
    trans.save()

    update_balance(trans)

    return redirect('/t/')

    #return HttpResponse("add,,,,You're looking at question %s." +  request.POST['name'])
    #return HttpResponse("add,,,,You're looking at question %s.", request)
    
def delete(request):
    return HttpResponse("deleted %s." +  str(len(request.POST['cb'])))


#---
def update_balance(trans):
    # update balance---
    prevTrans = Trans.objects.filter(pmethod=trans.pmethod, user=trans.user, date__lt=trans.date).order_by('date')[:1]

    prevBalance = 0
    if len(prevTrans) != 0:
        prevBalance = prevTrans[0].balance

    # get newer transs--
    transs = Trans.objects.filter(pmethod=trans.pmethod, user=trans.user, date__gte=trans.date).order_by('date')

    for t in transs:
        print(t.name)
        t.balance = prevBalance - t.expense
        t.save()

        prevBalance = t.balance
        
    #hoge

    #TODO update balance multiple trans
    
    
    #hoge
    




# pmethod-----------------------
def index_pmethod(request):
    #pmethod_list = Pmethod.objects.order_by('-group')
    #pmethod_list = Pmethod.objects.order_by('-order')[:30]
    pmgroup_list = PmethodGroup.objects.order_by('order')

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

    pmgroup_list = PmethodGroup.objects.order_by('-order')[:30]

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
        print ('hoge')

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
    pgmethod = PmethodGroup(name=request.POST['name'])
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

    pmgs = PmethodGroup.objects.order_by('-order')

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
        print ('hoge')

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






