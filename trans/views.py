import datetime

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template import loader

from .models import Trans, PmethodGroup, Pmethod


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
    context = {'latest_trans_list': latest_trans_list}
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
    today = datetime.date.today()

    trans = Trans(name=request.POST['name'],date=today)
    trans.save()
    #q = Question(question_text=request.POST['name'],pub_date=today)
    #q.save()
                        
    return HttpResponse("add,,,,You're looking at question %s." +  request.POST['name'])
    #return HttpResponse("add,,,,You're looking at question %s.", request)
    
def delete(request):
    return HttpResponse("deleted %s." +  str(len(request.POST['cb'])))
    


# pmethod-----------------------
def index_pmethod(request):
    pmethod_list = Pmethod.objects.order_by('-id')[:30]
    pmgroup_list = PmethodGroup.objects.order_by('-id')[:30]

    context = {'pmethod_list': pmethod_list, 'pmgroup_list': pmgroup_list}
    return render(request, 'trans/index_pmethod.html', context)

#pmgroup------------------------------
def add_pmgroup(request):
    pgmethod = PmethodGroup(name=request.POST['name'])
    pgmethod.save()
                        
    return HttpResponse("add,,,,You're looking at question %s." +  request.POST['name'])

def delete_pmgroup(request, pmgroup_id):
    pmg = PmethodGroup.objects.get(pk=pmgroup_id).delete()

    return HttpResponse("deleted payment method group %s." +  pmgroup_id)





