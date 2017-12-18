from django.conf.urls import url

from . import views

app_name = 'trans'
urlpatterns = [
    # header
    url(r'^list$', views.list, name='list'),
    url(r'^monthlyreport$', views.monthlyreport, name='monthlyreport'),
    url(r'^advanced$', views.advanced, name='advanced'),

    #trans
    url(r'^$', views.index, name='index'),
    url(r'^add$', views.add, name='add'),
    url(r'^delete$', views.delete, name='delete'),
    url(r'^multi_trans_select$', views.multi_trans_select, name='multi_trans_select'),

    # for ajax
    url(r'^sum_expense$', views.sum_expense, name='sum_expense'),

    # suica
    url(r'^suica_upload$', views.suica_upload, name='suica_upload'),
    url(r'^suica_check$', views.suica_check, name='suica_check'),
    
    # jaccs
    url(r'^jaccs_upload$', views.jaccs_upload, name='jaccs_upload'),
    url(r'^jaccs_check$', views.jaccs_check, name='jaccs_check'),
    
    # salary
    url(r'^salary_upload$', views.salary_upload, name='salary_upload'),
    url(r'^salary_check$', views.salary_check, name='salary_check'),
    
    # everymonth
    url(r'^everymonth$', views.everymonth, name='everymonth'),

    
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

    #for select option update
    url(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/list/$', views.list_pmgroup, name='list_pmgroup'),



    #category
    #url(r'^category$', views.index_category, name='index_category'),
    url(r'^category/add$', views.add_category, name='add_category'),
    url(r'^category/(?P<category_id>[0-9]+)/$', views.edit_category, name='edit_category'),
    url(r'^category/(?P<category_id>[0-9]+)/update/$', views.update_category, name='update_category'),
    url(r'^category/(?P<category_id>[0-9]+)/delete/$', views.delete_category, name='delete_category'),
    url(r'^category/(?P<category_id>[0-9]+)/up/$', views.up_category, name='up_category'),



    #categorygroup
    url(r'^categorygroup/add$', views.add_categorygroup, name='add_categorygroup'),
    url(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/$', views.edit_categorygroup, name='edit_categorygroup'),
    url(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/update/$', views.update_categorygroup, name='update_categorygroup'),
    url(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/delete/$', views.delete_categorygroup, name='delete_categorygroup'),
    url(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/up/$', views.up_categorygroup, name='up_categorygroup'),

    #for select option update
    url(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/list/$', views.list_categorygroup, name='list_categorygroup'),

    



]
