from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from store import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('store.urls')),
    path('admin/', admin.site.urls),
    # Главная страница и магазин
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.cart, name='cart'),
   

    # Регистрация, вход и выход
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='store/logout.html'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
