from django.conf.urls import url

from . import views

app_name = 'trans'
urlpatterns = [
    #trans
    url(r'^$', views.index, name='index'),
    url(r'^add$', views.add, name='add'),
    url(r'^delete$', views.delete, name='delete'),

    #pmethod
    url(r'^pmethod$', views.index_pmethod, name='index_pmethod'),
    url(r'^pmethod/add$', views.add_pmethod, name='add_pmethod'),
    url(r'^pmethod/(?P<pmethod_id>[0-9]+)/$', views.edit_pmethod, name='edit_pmethod'),
    url(r'^pmethod/(?P<pmethod_id>[0-9]+)/update/$', views.update_pmethod, name='update_pmethod'),
    url(r'^pmethod/(?P<pmethod_id>[0-9]+)/delete/$', views.delete_pmethod, name='delete_pmethod'),
    url(r'^pmethod/(?P<pmethod_id>[0-9]+)/up/$', views.up_pmethod, name='up_pmethod'),


    #pmgroup
    url(r'^pmgroup/add$', views.add_pmgroup, name='add_pmgroup'),
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/$', views.edit_pmgroup, name='edit_pmgroup'),
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/update/$', views.update_pmgroup, name='update_pmgroup'),
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/delete/$', views.delete_pmgroup, name='delete_pmgroup'),
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/up/$', views.up_pmgroup, name='up_pmgroup'),



]
