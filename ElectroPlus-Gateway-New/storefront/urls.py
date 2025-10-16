from django.urls import path
from . import views

app_name = 'storefront'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Carrito
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<slug:slug>/', views.cart_add, name='cart_add'),
    path('carrito/actualizar/<int:product_id>/', views.cart_update, name='cart_update'),
    path('carrito/eliminar/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
    # Checkout y Pedidos
    path('checkout/', views.checkout, name='checkout'),
    path('pedidos/', views.order_history, name='order_history'),
    path('pedidos/<int:order_id>/cancelar/', views.cancel_order, name='cancel_order'),
    
    # Lista de deseos
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Perfil de usuario
    path('perfil/', views.profile, name='profile'),
    
    # API para reseñas
    path('api/reviews/add/<int:product_id>/', views.add_review, name='add_review'),
    # Reseñas
    path('review/add/<int:product_id>/', views.add_review, name='add_review'),

    # Chatbot
    path('chatbot/', views.chatbot, name='chatbot'),
    path('api/chatbot/', views.chatbot_response, name='chatbot_response'),
]