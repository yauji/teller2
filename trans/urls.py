from django.conf.urls import url

from . import views

app_name = 'trans'
urlpatterns = [
    # ex: /polls/
    url(r'^$', views.index, name='index'),
    # ex: /polls/5/
    #url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    # ex: /polls/5/results/
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
    #url(r'^$', views.index, name='index'),

    #trans
    url(r'^add$', views.add, name='add'),
    url(r'^delete$', views.delete, name='delete'),

    #pmethod
    url(r'^pmethod$', views.index_pmethod, name='index_pmethod'),

    #pmgroup
    url(r'^pmgroup/add$', views.add_pmgroup, name='add_pmgroup'),
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/delete/$', views.delete_pmgroup, name='delete_pmgroup'),

]
