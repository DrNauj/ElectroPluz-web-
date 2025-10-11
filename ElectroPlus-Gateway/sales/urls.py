from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.shop_home, name='shop_home'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('api/cart/add/', views.cart_add, name='cart_add'),
    path('api/cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('api/cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('api/process-order/', views.process_order, name='process_order'),
]