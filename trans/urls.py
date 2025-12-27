from django.urls import re_path
# from django.conf.urls import url

from . import views

app_name = 'trans'
urlpatterns = [
    # header
    re_path(r'^list$', views.list, name='list'),
    re_path(r'^monthlyreport$', views.monthlyreport, name='monthlyreport'),
    re_path(r'^advanced$', views.advanced, name='advanced'),

    # trans
    re_path(r'^$', views.index, name='index'),
    re_path(r'^add$', views.add, name='add'),
    re_path(r'^delete$', views.delete, name='delete'),
    re_path(r'^multi_trans_select$', views.multi_trans_select,
            name='multi_trans_select'),
    re_path(r'^trans_update$', views.trans_update, name='trans_update'),

    # for ajax
    re_path(r'^sum_expense$', views.sum_expense, name='sum_expense'),

    # suica
    re_path(r'^suica_upload$', views.suica_upload, name='suica_upload'),
    re_path(r'^suica_check$', views.suica_check, name='suica_check'),

    # jaccs
    re_path(r'^jaccs_upload$', views.jaccs_upload, name='jaccs_upload'),
    re_path(r'^jaccs_upload_new$', views.jaccs_upload_new, name='jaccs_upload_new'),
    re_path(r'^jaccs_check$', views.jaccs_check, name='jaccs_check'),

    # rakuten card
    re_path(r'^rakutencard_upload$', views.rakutencard_upload,
            name='rakutencard_upload'),
    re_path(r'^rakutencard_check$', views.rakutencard_check,
            name='rakutencard_check'),

    # Shinsei bank
    re_path(r'^shinsei_upload$', views.shinsei_upload,
            name='shinsei_upload'),
    re_path(r'^shinsei_check$', views.shinsei_check,
            name='shinsei_check'),

    # salary
    re_path(r'^salary_upload$', views.salary_upload, name='salary_upload'),
    re_path(r'^salary_check$', views.salary_check, name='salary_check'),

    # everymonth
    re_path(r'^everymonth$', views.everymonth, name='everymonth'),


    # annual report
    re_path(r'^annualreport$', views.annualreport, name='annualreport'),

    # total balance
    re_path(r'^totalbalance$', views.totalbalance, name='totalbalance'),

    # shared expense
    re_path(r'^sharedexpense$', views.sharedexpense, name='sharedexpense'),



    # pmethod
    re_path(r'^pmethod$', views.index_pmethod, name='index_pmethod'),
    re_path(r'^pmethod/add$', views.add_pmethod, name='add_pmethod'),
    re_path(r'^pmethod/(?P<pmethod_id>[0-9]+)/$',
            views.edit_pmethod, name='edit_pmethod'),
    re_path(r'^pmethod/(?P<pmethod_id>[0-9]+)/update/$',
            views.update_pmethod, name='update_pmethod'),
    re_path(r'^pmethod/(?P<pmethod_id>[0-9]+)/delete/$',
            views.delete_pmethod, name='delete_pmethod'),
    re_path(r'^pmethod/(?P<pmethod_id>[0-9]+)/up/$',
            views.up_pmethod, name='up_pmethod'),


    # pmgroup
    re_path(r'^pmgroup/add$', views.add_pmgroup, name='add_pmgroup'),
    re_path(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/$',
            views.edit_pmgroup, name='edit_pmgroup'),
    re_path(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/update/$',
            views.update_pmgroup, name='update_pmgroup'),
    re_path(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/delete/$',
            views.delete_pmgroup, name='delete_pmgroup'),
    re_path(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/up/$',
            views.up_pmgroup, name='up_pmgroup'),

    # for select option update
    re_path(r'^pmgroup/(?P<pmgroup_id>[0-9]+)/list/$',
            views.list_pmgroup, name='list_pmgroup'),



    # category
    # re_path(r'^category$', views.index_category, name='index_category'),
    re_path(r'^category/add$', views.add_category, name='add_category'),
    re_path(r'^category/(?P<category_id>[0-9]+)/$',
            views.edit_category, name='edit_category'),
    re_path(r'^category/(?P<category_id>[0-9]+)/update/$',
            views.update_category, name='update_category'),
    re_path(r'^category/(?P<category_id>[0-9]+)/delete/$',
            views.delete_category, name='delete_category'),
    re_path(r'^category/(?P<category_id>[0-9]+)/up/$',
            views.up_category, name='up_category'),



    # categorygroup
    re_path(r'^categorygroup/add$', views.add_categorygroup,
            name='add_categorygroup'),
    re_path(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/$',
            views.edit_categorygroup, name='edit_categorygroup'),
    re_path(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/update/$',
            views.update_categorygroup, name='update_categorygroup'),
    re_path(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/delete/$',
            views.delete_categorygroup, name='delete_categorygroup'),
    re_path(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/up/$',
            views.up_categorygroup, name='up_categorygroup'),

    # for select option update
    re_path(r'^categorygroup/(?P<categorygroup_id>[0-9]+)/list/$',
            views.list_categorygroup, name='list_categorygroup'),





]
