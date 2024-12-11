from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, Order, OrderItem
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.urls import reverse

def home(request):
    # Получаем только первые 10 товаров
    products = Product.objects.all()[:6]
    cart_items = Cart.objects.filter(user=request.user).values_list('product_id', 'quantity') if request.user.is_authenticated else []
    cart_dict = {item[0]: item[1] for item in cart_items}  # Словарь вида {product_id: quantity}
    
    return render(request, 'store/home.html', {
        'products': products,
        'cart_dict': cart_dict  # Передаем словарь с количеством товаров в корзине
    })

def product_list(request):
    # Получаем значение поля поиска из запроса
    search_query = request.GET.get('search', '')
    
    # Фильтруем продукты по имени
    products = Product.objects.filter(name__icontains=search_query)
    
    cart_items = Cart.objects.filter(user=request.user).values_list('product_id', 'quantity') if request.user.is_authenticated else []
    cart_dict = {item[0]: item[1] for item in cart_items}  # Словарь вида {product_id: quantity}
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'cart_dict': cart_dict,  # Передаем словарь с количеством товаров в корзине
        'search_query': search_query,  # Передаем значение поиска в шаблон
    })


def is_admin(user):
    return user.is_staff

def is_owner_or_admin(user, order_user):
    return user.is_staff or user == order_user

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            transfer_cart_to_user(request)  # Переносим корзину
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'store/register.html', {'form': form})


@login_required
def add_to_cart_ajax(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            if request.user.is_authenticated:
                cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
                cart_item.save()
                return JsonResponse({'status': 'ok', 'quantity': cart_item.quantity})
            else:
                # Добавляем товар в сессию для неавторизованных пользователей
                if 'cart' not in request.session:
                    request.session['cart'] = {}
                if product_id in request.session['cart']:
                    request.session['cart'][product_id] += 1
                else:
                    request.session['cart'][product_id] = 1
                
                request.session.modified = True
                return JsonResponse({'status': 'ok', 'quantity': request.session['cart'][product_id]})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Товар не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'}, status=400)

@login_required
def transfer_cart_to_user(request):
    if 'cart' in request.session:
        for product_id, quantity in request.session['cart'].items():
            product = get_object_or_404(Product, id=product_id)
            cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
            cart_item.quantity += quantity
            cart_item.save()
        # Удаляем корзину из сессии после переноса
        del request.session['cart']
        request.session.modified = True

@login_required
def update_cart_quantity_ajax(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity_change = int(request.POST.get('quantity_change', 0))
        try:
            product = Product.objects.get(id=product_id)
            cart_item = Cart.objects.get(user=request.user, product=product)
            cart_item.quantity += quantity_change
            if cart_item.quantity <= 0:
                cart_item.delete()  # Удалить товар, если его количество меньше или равно 0
            else:
                cart_item.save()
            return JsonResponse({'status': 'ok', 'quantity': cart_item.quantity if cart_item.quantity > 0 else 0})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Товар не найден'})
    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'})

@login_required
def remove_from_cart_ajax(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            cart_item = Cart.objects.get(user=request.user, product_id=product_id)
            cart_item.delete()
            return JsonResponse({'status': 'ok', 'message': 'Товар удален из корзины'})
        except Cart.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Товар не найден в корзине'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'}, status=400)

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Получаем все уникальные электронные почты пользователей
    emails = User.objects.values_list('email', flat=True).distinct()

    if request.method == 'POST':
        # Валидация данных, если форма отправлена
        email = request.POST.get('email')
        game_username = request.POST.get('game_username')
        telegram_username = request.POST.get('telegram_username')
        agree_terms = request.POST.get('agree_terms', 'off')

        if not all([email, game_username, telegram_username, agree_terms == 'on']):
            return JsonResponse({'status': 'error', 'message': 'Заполните все поля и подтвердите согласие с условиями.'}, status=400)

        # Создание заказа
        order = Order.objects.create(
            user=request.user,
            email=email,
            price=total_price,
            game_username=game_username,
            telegram_username=telegram_username,
            status = "Created"
        )

        # Создаем OrderItem для каждого товара в корзине
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        # Удаление всех товаров из корзины после создания заказа
        cart_items.delete()  # Удаляем все элементы корзины пользователя

        request.session['order_info'] = {
            'email': email,
            'game_username': game_username,
            'telegram_username': telegram_username,
        }

        return JsonResponse({
            'status': 'success',
            'message': 'Заявка на оплату отправлена, ожидайте!',
            'redirect_url': f'/payment-confirmation/{order.id}/'  # URL перенаправления на страницу подтверждения
        }) 

    # Если запрос GET, просто возвращаем шаблон с корзиной и email
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'emails': emails
    })


@login_required
def payment_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)  # Получаем конкретный заказ
    
    # Проверяем, является ли текущий пользователь создателем заказа или администратором
    if not is_owner_or_admin(request.user, order.user):
        return redirect('home')
    
    request.session['order_info'] = {
        'email': order.email,
        'game_username': order.game_username,
        'telegram_username': order.telegram_username,
    }
    return render(request, 'store/payment_confirmation.html', {'order': order})


@login_required
@user_passes_test(is_admin)
def admin_order_requests(request):
    orders = Order.objects.prefetch_related("items__product").exclude(status__in=["Completed", "Rejected"])  # Предварительная загрузка продуктов
    return render(request, 'store/admin_order_requests.html', {'orders': orders})

@login_required
@user_passes_test(is_admin)
def reject_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.status = "Rejected"
        order.save()  # Сохраняем изменения
        return JsonResponse({'status': 'success', 'message': 'Заказ отклонён.'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Заказ не найден.'}, status=404)
    
@login_required
@user_passes_test(is_admin)
def send_link(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        order.link_sent = True  # Обновляем статус
        order.status = "In progress"
        order.save()  # Сохраняем изменения
        return JsonResponse({'status': 'success', 'message': 'Ссылка отправлена.'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Заказ не найден.'}, status=404)

@login_required
@user_passes_test(is_admin)
def complete_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        order.status = "Completed"  # Обновляем статус на "Completed"
        order.save()  # Сохраняем изменения
        return JsonResponse({'status': 'success', 'message': 'Статус заказа обновлен.'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Заказ не найден.'}, status=404)

@login_required
@user_passes_test(is_admin)
def order_history(request):
    # Загружаем все заказы для страницы истории
    orders = Order.objects.all().order_by('-created_at')  
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def my_orders(request):
    # Получаем все заказы текущего пользователя, отсортированные по id в обратном порядке
    orders = Order.objects.filter(user=request.user).order_by('-id').prefetch_related('items__product')

    return render(request, 'store/my_orders.html', {
        'orders': orders
    })