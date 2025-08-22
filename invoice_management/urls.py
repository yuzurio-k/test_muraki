from django.urls import path
from . import views

urlpatterns = [
    # ダッシュボード
    path('', views.dashboard, name='dashboard'),
    
    # 取引先会社関連
    path('companies/', views.company_list, name='company_list'),
    path('companies/add/', views.company_add, name='company_add'),
    path('companies/<int:pk>/edit/', views.company_edit, name='company_edit'),
    
    # ユーザー関連（管理者のみ）
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/password/', views.user_password_change, name='user_password_change'),
    
    # 請求書関連
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_add, name='invoice_add'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    
    # レポート
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/analytics/', views.analytics_report, name='analytics_report'),
    path('reports/monthly-detail/', views.monthly_detail_report, name='monthly_detail_report'),
    path('reports/company-detail/', views.company_detail_report, name='company_detail_report'),
]
