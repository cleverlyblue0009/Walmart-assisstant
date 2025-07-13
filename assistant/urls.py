from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('get_response/', views.get_response, name='get_response'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-register/', views.admin_register, name='admin_register'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('store-map/', views.store_map, name='store_map'),
    path('analyze_image/', views.analyze_image, name='analyze_image'),
    path('category/<str:category_name>/', views.view_category, name='view_category'),

]
