from django.urls import path

from . import views

urlpatterns = [
    # path('', views.contacts, name='contacts'),
    path('', views.login, name='login'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('register/', views.register, name='register'),
    path('change_password/', views.change_password, name='change_password'),
    path('admin/<str:passkey>/', views.admin, name='admin'),
    path('admin/<str:passkey>/admin_op/', views.admin_op, name='admin_op'),
    path('admin/<str:passkey>/admin_oa/', views.admin_oa, name='admin_oa'),
    path('contacts/<str:passkey>/', views.contacts, name='contacts'),
    path('contacts/<str:passkey>/search/', views.search, name='search'),
    path('contacts/<str:passkey>/profile/', views.profile, name='profile'),
    path('contacts/<str:passkey>/update_profile/', views.update_profile, name='update_profile'),
    path('contacts/<str:passkey>/add/', views.add_contact, name='add'),
    path('contacts/<str:passkey>/addOA/', views.add_oa, name='addOA'),
    path('contacts/<str:passkey>/add_group/', views.add_group, name='add_group'),
    path('contacts/<str:passkey>/delete_group/', views.delete_group, name='delete_group'),
    path('contacts/<str:passkey>/<str:wechat_id>/', views.detail, name='detail'),
    path('contacts/<str:passkey>/<str:wechat_id>/delete/', views.delete_contact, name='delete'),
    path('contacts/<str:passkey>/<str:wechat_id>/update/', views.update_contact, name='update'),
]
