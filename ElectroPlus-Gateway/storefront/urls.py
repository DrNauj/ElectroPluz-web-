from django.urls import path
from . import views

app_name = 'storefront'

urlpatterns = [
    # Páginas principales
    path('', views.home, name='home'),
    path('productos/', views.product_list, name='products'),
    path('producto/<slug:slug>/', views.product_detail, name='product'),
    path('categoria/<slug:slug>/', views.category, name='category'),
    path('buscar/', views.search, name='search'),
    path('ofertas/', views.ofertas, name='ofertas'),
    
    # Carrito y compra
    path('carrito/', views.cart, name='cart'),
    path('carrito/agregar/', views.cart_add, name='cart_add'),
    path('carrito/actualizar/', views.cart_update, name='cart_update'),
    path('carrito/eliminar/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirmar/', views.checkout_confirm, name='checkout_confirm'),
    
    # Perfil y pedidos
    path('perfil/', views.profile, name='profile'),
    path('perfil/editar/', views.api_profile_edit, name='profile_edit'),
    path('pedidos/', views.orders, name='orders'),
    path('pedido/<str:order_id>/', views.order_detail, name='order_detail'),
    
    # Páginas de información
    path('sobre-nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('envios/', views.shipping, name='shipping'),
    path('devoluciones/', views.returns, name='returns'),
    path('garantia/', views.warranty, name='warranty'),
    path('privacidad/', views.privacy, name='privacy'),
    path('terminos/', views.terms, name='terms'),
    
    # API endpoints
    path('api/cart/add/', views.api_cart_add, name='api_cart_add'),
    path('api/cart/update/', views.api_cart_update, name='api_cart_update'),
    path('api/cart/remove/', views.api_cart_remove, name='api_cart_remove'),
    path('api/cart/count/', views.api_get_cart_count, name='api_cart_count'),
    path('api/cart/total/', views.api_get_cart_total, name='api_cart_total'),
    path('api/checkout/validate/', views.api_checkout_validate, name='api_checkout_validate'),
    path('api/validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('api/search/suggestions/', views.search_suggestions, name='search_suggestions'),
]