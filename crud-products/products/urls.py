# products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),

    # Products CRUD
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # CSV
    path('products/export/', views.product_export_csv, name='product_export_csv'),
    path('products/import/', views.product_import_csv, name='product_import_csv'),
    path('products/csv-template/', views.product_csv_template,
         name='product_csv_template'),
]
