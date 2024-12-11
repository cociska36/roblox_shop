from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('products/', views.product_list, name='product_list'),  # Страница всех товаров
    path('cart/', views.cart, name='cart'),  # Корзина
    # Удаляем или закомментируем следующий маршрут
    # path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  
    path('add-to-cart-ajax/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('update-cart-quantity-ajax/', views.update_cart_quantity_ajax, name='update_cart_quantity_ajax'),
    path('transfer-cart/', views.transfer_cart_to_user, name='transfer_cart'),
    path('remove-from-cart/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('payment-confirmation/<int:order_id>/', views.payment_confirmation, name='payment_confirmation'),
    path('admin-order-requests/', views.admin_order_requests, name='admin_order_requests'),
    path('reject-order/<int:order_id>/', views.reject_order, name='reject_order'),
    path('send-link/<int:order_id>/', views.send_link, name='send_link'),
    path('complete-order/<int:order_id>/', views.complete_order, name='complete_order'),
    path('order-history/', views.order_history, name='order_history'),
]
