from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model  
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import ZeUser
from .models import Product, Banner, Notice 
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from core.models import Cart, Wishlist
from .models import ShippingAddress
from .models import Product, ShippingAddress, Order
from django.http import JsonResponse
from .models import Cart, Wishlist, Product
from .models import Category, Brand, ShopProductDescription
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ProductDetails
from .forms import ProductDetailsForm
from django.db.models import Q
from django.db import models
from django.http import JsonResponse
from django.db.models import Avg
import datetime
from datetime import datetime

import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile




User = get_user_model() 

def login_view(request):
    login_errors = None
    email_or_username = ''  # default empty

    if request.method == "POST":
        email_or_username = request.POST.get("email")  # user input
        password = request.POST.get("password")

        # First try authenticate using username
        user = authenticate(request, username=email_or_username, password=password)

        if user is None:
            # If not found, try email
            try:
                u = User.objects.get(email=email_or_username)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            login_errors = "Invalid email or password."

    context = {
        "login_errors": login_errors,
        "email": email_or_username,
        "show_signin": True,  # show login form
    }
    return render(request, "core/signup.html", context)

# Signup view
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'core/signup.html', {
                'signup_error': 'Username already exists! Please choose another.',
                'username': username,
                'email': email,
                'show_signin': False,  
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'core/signup.html', {
                'signup_error': 'Email already exists! Please use a different email.',
                'username': username,
                'email': email,
                'show_signin': False,
            })

        if password1 != password2:
            return render(request, 'core/signup.html', {
                'signup_error': 'Passwords do not match!',
                'username': username,
                'email': email,
                'show_signin': False,
            })

        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        messages.success(request, "Account created successfully! Please sign in.")

        # Render template with signin form visible
        return render(request, 'core/signup.html', {
            'show_signin': True,  
            'email': email,       
        })

    # Default: show signup form
    return render(request, 'core/signup.html', {'show_signin': False})



def inline_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_pass1 = request.POST.get('new_password1')
        new_pass2 = request.POST.get('new_password2')

        if new_pass1 != new_pass2:
            messages.error(request, "Passwords do not match.")
            return redirect('login')

        try:
            user = User.objects.get(email=email)
            user.set_password(new_pass1)
            user.save()
            login(request, user)  
            messages.success(request, "Password updated successfully! You are now signed in.")
            return redirect('dashboard')  
        except User.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect('login')
    return redirect('login')

def home(request):
    # ---------------- Banners & Notices ----------------
    banners = Banner.objects.all().order_by('-created_at')
    notices = Notice.objects.all().order_by('-created_at')[:5]

    # ---------------- ShopProduct Data ----------------
    latest_products = ShopProduct.objects.filter(latest_launch=True)[:10]
    best_deals = ShopProduct.objects.filter(best_deal=True)[:10]
    other_products = ShopProduct.objects.filter(latest_launch=False, best_deal=False)[:10]

    # ---------------- Similar Products ----------------
    similar_products = ShopProduct.objects.filter(is_home_similar=True)

    # ---------------- Final Price Calculation ----------------
    for product_list in [latest_products, best_deals, other_products, similar_products]:
        for product in product_list:
            if product.discount:
                product.final_price = product.price - (product.price * product.discount / 100)
            else:
                product.final_price = product.price

    # ---------------- Render Template ----------------
    context = {
        'banners': banners,
        'latest_products': latest_products,
        'best_deals': best_deals,
        'other_products': other_products,
        'similar_products': similar_products,
        'notices': notices,
    }
    return render(request, 'core/home.html', context)

from django.db.models import Sum
def shop_page(request):
    products = ShopProduct.objects.all()

    # Category-wise grouping
    products_by_category = {}
    for product in products:
        category_name = product.product.name  

        if category_name not in products_by_category:
            products_by_category[category_name] = []

        # Colors ko list me convert
        if product.colors:
            product.color_list = product.colors.split(',')
        else:
            product.color_list = []

        # Calculate available quantity
        booked_qty = Order.objects.filter(
            product=product,
            status__in=['Pending', 'Shipped']
        ).aggregate(total=Sum('quantity'))['total'] or 0

        product.available_quantity = product.quantity - booked_qty

        # Discounted price
        if product.discount:
            product.discounted_price = product.price * (100 - product.discount) / 100
        else:
            product.discounted_price = product.price

        products_by_category[category_name].append(product)

    return render(request, 'core/shop.html', {
        'products_by_category': products_by_category
    })





from rapidfuzz import fuzz


def search_products(request):
    query = request.GET.get('q', '').strip()
    products_by_category = {}

    if query:
        all_products = ShopProduct.objects.all()
        matched_products = []

        query_words = query.lower().split()

        for product in all_products:
            name_lower = product.name.lower()
            brand_lower = product.brand.name.lower()
            product_type_lower = product.product.name.lower() if product.product else ''

            word_matches = []
            for word in query_words:
                # fuzzy match har field ke sath
                score_name = fuzz.partial_ratio(word, name_lower)
                score_brand = fuzz.partial_ratio(word, brand_lower)
                score_product = fuzz.partial_ratio(word, product_type_lower)

                # agar kisi bhi field me 70+ similarity ho to match
                if max(score_name, score_brand, score_product) >= 70:
                    word_matches.append(True)
                else:
                    word_matches.append(False)

            # agar sab words ka match true ho to product add karo
            if all(word_matches):
                matched_products.append(product)

        # group by category
        for product in matched_products:
            category_name = product.product.name if product.product else "Other"
            if category_name not in products_by_category:
                products_by_category[category_name] = []
            products_by_category[category_name].append(product)

    if not products_by_category:
        return render(request, 'core/no_result.html', {'query': query})

    return render(request, 'core/shop.html', {'products_by_category': products_by_category})



def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'category_products.html', {
        'category': category,
        'products': products
    })





def mobile_products(request):
    category = get_object_or_404(Category, name__iexact='Mobile')
    products = ShopProduct.objects.filter(product__name__iexact='Mobile')[:15]

    # Calculate discounted price for each product
    for p in products:
        if p.discount:
            p.discounted_price = round(p.price - (p.price * p.discount / 100), 2)
        else:
            p.discounted_price = p.price

    return render(request, "core/category/mobile_products.html", {
        "products": products,
        "category_name": category.name
    })

def computer_hardware_products(request):
    category = get_object_or_404(Category, name='Computer Hardware')
    products = ShopProduct.objects.filter(product__name__iexact='Computer Hardware')[:15]

    # discounted_price calculate kar ke add karo
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount / 100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/computer_hardware_products.html", {
        "products": products,
        "category_name": category.name
    })


def tv_products(request):
    category = get_object_or_404(Category, name='LED/OLED TV')
    products = ShopProduct.objects.filter(product__name__iexact='LED/OLED TV')[:15]

    # Calculate discounted price
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount / 100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/tv_products.html", {
        "products": products,
        "category_name": category.name
    })


def soundbar_products(request):
    category = get_object_or_404(Category, name='Soundbar')
    products = ShopProduct.objects.filter(product__name__iexact='Soundbar')[:15]

    # Har product ke liye discounted_price calculate karo
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/soundbar_products.html", {
        "products": products,
        "category_name": category.name
    })


def speaker_products(request):
    category = get_object_or_404(Category, name='Speaker')
    products = ShopProduct.objects.filter(product__name__iexact='Speaker')[:15]

    # Discounted price calculate karo
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/speaker_products.html", {
        "products": products,
        "category_name": category.name
    })


def laptop_products(request):
    category = get_object_or_404(Category, name='Laptop')
    products = ShopProduct.objects.filter(product__name__iexact='Laptop')[:15]
    # Discounted price calculate karo
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/laptop_products.html", {
        "products": products,
        "category_name": category.name
    })

def projector_products(request):
    category = get_object_or_404(Category, name='Projector')
    products = ShopProduct.objects.filter(product__name__iexact='Projector')[:15]
    # Discounted price calculate karo
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/projector_products.html", {
        "products": products,
        "category_name": category.name
    })

def headphones_products(request):
    category = get_object_or_404(Category, name='Headphones')
    products = ShopProduct.objects.filter(product__name__iexact='Headphones')[:15]
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/headphones_products.html", {
        "products": products,
        "category_name": category.name
    })

def camera_products(request):
    category = get_object_or_404(Category, name='Camera')
    products = ShopProduct.objects.filter(product__name__iexact='Camera')[:15]
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/camera_products.html", {
        "products": products,
        "category_name": category.name
    })

def smartwatch_products(request):
    category = get_object_or_404(Category, name='Smartwatch')
    products = ShopProduct.objects.filter(product__name__iexact='Smartwatch')[:15]
    for product in products:

        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/smartwatch_products.html", {
        "products": products,
        "category_name": category.name
    })

def gaming_products(request):
    category = get_object_or_404(Category, name='Gaming')
    products = ShopProduct.objects.filter(product__name__iexact='Gaming')[:15]
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/gaming_products.html", {
        "products": products,
        "category_name": category.name
    })

def wifi_router_products(request):
    category = get_object_or_404(Category, name='WiFi Router')
    products = ShopProduct.objects.filter(product__name__iexact='WiFi Router')[:15]
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/wifi_products.html", {
        "products": products,
        "category_name": category.name
    })

def smart_home_devices_products(request):
    category = get_object_or_404(Category, name='Smart Home Device')
    products = ShopProduct.objects.filter(product__name__iexact='Smart Home Device')[:15]
    for product in products:
        if product.discount:
            product.discounted_price = product.price * (1 - product.discount/100)
        else:
            product.discounted_price = product.price

    return render(request, "core/category/smarthome_products.html", {
        "products": products,
        "category_name": category.name
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Calculate discounted price
    if product.discount:
        product.final_price = product.price - (product.price * product.discount / 100)
    else:
        product.final_price = product.price

    return render(request, 'core/product_detail.html', {'product': product})

def category_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    details = ProductDetails.objects.filter(product=product)

    # Discount price calculation
    if product.discount:
        final_price = product.price - (product.price * product.discount / 100)
    else:
        final_price = product.price

    return render(request, 'core/category_details.html', {
        'product': product,
        'details': details,
        'final_price': final_price
    })


def add_product_details(request):
    if request.method == 'POST':
        form = ProductDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_product_details')
    else:
        form = ProductDetailsForm()
    return render(request, 'backend/add_product_details.html', {'form': form})

# Manage Product Details
def manage_product_details(request):
    details = ProductDetails.objects.all()
    return render(request, 'backend/manage_product_details.html', {'details': details})

# Edit Product Details
from django.shortcuts import render, redirect, get_object_or_404
from .models import ProductDetails, Product, Color

def edit_product_details(request, id):
    detail = get_object_or_404(ProductDetails, id=id)
    products = Product.objects.all()
    colors = Color.objects.all()  # Ye colors template me checkbox ke liye pass karenge

    if request.method == "POST":
        detail.product_id = request.POST.get('product')
        detail.stock = request.POST.get('stock')
        detail.specifications = request.POST.get('specifications')
        detail.description = request.POST.get('description')
        detail.warranty = request.POST.get('warranty')
        
        if request.FILES.get('image'):
            detail.image = request.FILES.get('image')
        
        detail.save()

        selected_colors = request.POST.getlist('colors')  # Ye list of IDs
        detail.colors.set(selected_colors)

        return redirect('manage_product_details')

    return render(request, 'backend/edit_product_details.html', {
        'detail': detail,
        'products': products,
        'colors': colors
    })


def delete_product_details(request, id):
    detail = ProductDetails.objects.get(id=id)
    detail.delete()
    return redirect('manage_product_details')

    

def dashboard(request):
    user = request.user
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        gender = request.POST.get('gender')  

        user.username = username
        user.email = email
        user.phone = mobile
        user.gender = gender
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('dashboard')

    return render(request, 'core/dashboard.html')

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'core/order_history.html', context)


@login_required(login_url='login')
def buy_now(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)

    selected_color = request.GET.get('color', None)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if product.discount:
        discounted_price = product.price * (100 - product.discount) / 100
    else:
        discounted_price = product.price

    states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ]

    context = {
        'product': product,
        'discounted_price': discounted_price,
        'states': states,
        'cart_item': cart_item,
        'selected_color': selected_color,  
    }

    return render(request, 'core/buy_now.html', context)
    
@csrf_exempt
def save_address(request, product_id):
    try:
        product = get_object_or_404(ShopProduct, id=product_id)

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            address_id = request.POST.get('address_id')
            name = request.POST.get('name')
            mobile = request.POST.get('mobile')
            alt_mobile = request.POST.get('alt_mobile', '')
            pincode = request.POST.get('pincode')
            locality = request.POST.get('locality')
            address_text = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')

            if not (name and mobile and pincode and locality and address_text and city and state):
                return JsonResponse({'error': 'All required fields must be filled.'}, status=400)

            if address_id: 
                shipping_address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
                shipping_address.name = name
                shipping_address.mobile = mobile
                shipping_address.alt_mobile = alt_mobile
                shipping_address.pincode = pincode
                shipping_address.locality = locality
                shipping_address.address = address_text
                shipping_address.city = city
                shipping_address.state = state
                shipping_address.save()
                is_edit = True
            else:
                shipping_address = ShippingAddress.objects.create(
                    user=request.user,
                    name=name,
                    mobile=mobile,
                    alt_mobile=alt_mobile,
                    pincode=pincode,
                    locality=locality,
                    address=address_text,
                    city=city,
                    state=state
                )
                is_edit = False

            return JsonResponse({
                'id': shipping_address.id,
                'name': shipping_address.name,
                'mobile': shipping_address.mobile,
                'alt_mobile': shipping_address.alt_mobile,
                'address': shipping_address.address,
                'locality': shipping_address.locality,
                'city': shipping_address.city,
                'state': shipping_address.state,
                'pincode': shipping_address.pincode,
                'is_edit': is_edit
            })

        return JsonResponse({'error': 'Invalid request'}, status=400)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)



def set_delivery_address(request):
    if request.method == "POST" and request.user.is_authenticated:
        address_id = request.POST.get('address_id')
        try:
            # Sabse pehle selected address ko mark kare user ke liye
            # Optional: aapke model me 'is_delivery' field hona chahiye
            ShippingAddress.objects.filter(user=request.user).update(is_delivery=False)
            addr = ShippingAddress.objects.get(id=address_id, user=request.user)
            addr.is_delivery = True
            addr.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



from django.db import transaction

def payment_view(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    cart_item = Cart.objects.filter(product=product, user=request.user).first()

    # Discount calculation
    discounted_price = product.price
    if product.discount:
        discounted_price = product.price - (product.price * product.discount / 100)

    # Get selected color
    selected_color = request.GET.get("color", "")
    if cart_item and hasattr(cart_item, 'selected_color') and cart_item.selected_color:
        selected_color = cart_item.selected_color
    elif request.method == "POST":
        selected_color = request.POST.get("selected_color", selected_color)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "cod")

        # Shipping address
        address = ShippingAddress.objects.filter(user=request.user).last()
        if not address:
            messages.error(request, "Please add a shipping address before placing the order.")
            return redirect("add_shipping_address")

        # Quantity to order
        quantity_to_order = cart_item.quantity if cart_item else 1

        # Optional: Warn user if stock is low
        if product.quantity < quantity_to_order:
            messages.warning(request, f"⚠️ Only {product.quantity} units available for {product.name}. You can still place the order.")

        # ✅ Create order
        order = Order.objects.create(
            user=request.user,
            product=product,
            shipping_address=address,
            quantity=quantity_to_order,
            total_price=discounted_price,
            payment_method=payment_method,
            status="Pending",
            color=selected_color,
            order_confirmed=True,
            stock_reduced=False  # admin or signal will reduce stock
        )

        # ✅ Reduce stock quantity (added logic)
        if product.quantity >= quantity_to_order:
            product.quantity -= quantity_to_order
            product.save()
        else:
            messages.error(request, f"Insufficient stock for {product.name}.")

        # Remove from cart
        if cart_item:
            cart_item.delete()

        messages.success(request, "🎉 Order placed successfully!")
        return redirect("order_confirmation", order_id=order.id)

    context = {
        "product": product,
        "cart_item": cart_item,
        "discounted_price": discounted_price,
        "selected_color": selected_color,
    }
    return render(request, "core/payment.html", context)

def checkout_payment(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    shipping_addresses = ShippingAddress.objects.filter(user=request.user)

    # Assuming ki tumhare cart me color store hai
    cart_item = Cart.objects.filter(user=request.user, product=product).first()
    selected_color = cart_item.selected_color if cart_item else ''

    discounted_price = cart_item.price if cart_item else product.price

    context = {
        'product': product,
        'shipping_addresses': shipping_addresses,
        'cart_item': cart_item,
        'selected_color': selected_color,
        'discounted_price': discounted_price,
    }
    return render(request, 'core/checkout_payment.html', context)




def update_cart_quantity(request, product_id):
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product_id=product_id,
        defaults={'quantity': 1}
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "increase":
            cart_item.quantity += 1
        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1
        cart_item.save()

        # Check if AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'quantity': cart_item.quantity})

    # Fallback: normal redirect (agar browser normal submit kare)
    return redirect("buy_now", product_id=product_id)

def delete_address(request):
    if request.method == "POST" and request.user.is_authenticated:
        address_id = request.POST.get('id')
        if not address_id:
            return JsonResponse({'deleted': False, 'error': 'No ID'})
        try:
            addr = ShippingAddress.objects.get(id=address_id, user=request.user)
            addr.delete()
            return JsonResponse({'deleted': True})
        except ShippingAddress.DoesNotExist:
            return JsonResponse({'deleted': False, 'error': 'Address not found'})
    return JsonResponse({'deleted': False, 'error': 'Invalid request'})

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/order_confirmation.html', {'order': order})


# Return reason + comment form

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Order

def return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    reasons = [
        "Product damaged",
        "Wrong item received",
        "Item not as described",
        "Late delivery",
        "Quality not satisfactory",
        "Other issue"
    ]

    # Handle POST request (AJAX)
    if request.method == "POST":
        selected_reason = request.POST.get("reason")
        comment = request.POST.get("comment", "")

        if not selected_reason:
            return JsonResponse({'success': False, 'message': 'Please select a reason for return.'})

        if order.return_requested:
            return JsonResponse({'success': False, 'message': 'Return request already sent. Waiting for admin approval.'})

        if not order.delivered_date:
            return JsonResponse({'success': False, 'message': 'This order cannot be returned until it is delivered.'})

        # Save return request
        order.return_requested = True
        order.return_reason = selected_reason
        order.return_comment = comment
        order.return_status = 'pending'
        order.save()

        return JsonResponse({'success': True, 'message': 'Apka return request send ho gaya hai. Please wait for admin confirmation.'})

    # GET request → just render modal if needed
    return render(request, "core/return_request_modal.html", {"order": order, "reasons": reasons})

# Return confirmation page
def return_confirm(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Check if return has been requested
    if not order.return_requested:
        messages.warning(request, "You have not requested a return for this order yet.")
        return redirect('order_details', order_id=order.id)

    # Check if admin has accepted the return
    if order.return_status != 'accepted':
        messages.warning(request, "Your return request has not been approved by admin yet.")
        return redirect('order_details', order_id=order.id)

    # Only if approved, show the page
    reason = order.return_reason
    comment = order.return_comment

    return render(request, "core/return_confirm.html", {
        "order": order,
        "order_id": order.id,
        "product": order.product,
        "reason": reason,
        "comment": comment
    })


def process_return(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        status = request.POST.get("return_status")
        if status == "accepted":
            order.return_status = "accepted"
            date_str = request.POST.get("return_expected_date")
            if date_str:
                order.return_expected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            order.reject_reason = ""
        elif status == "rejected":
            order.return_status = "rejected"
            order.reject_reason = request.POST.get("reject_reason")
            order.return_expected_date = None
        order.save()

    return redirect("view_orders")

@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        message = "✅ Product added to wishlist!"
        success = True
    else:
        message = "❤️ Already in your wishlist!"
        success = False

    # Agar AJAX request hai to JSON return karo
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': success, 'message': message})
    
    # warna normal redirect
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))
    
@login_required(login_url='login')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)

    # Discounted price calculate karo
    for item in wishlist_items:
        if item.product.discount:
            item.product.final_price = item.product.price - (item.product.price * item.product.discount / 100)
        else:
            item.product.final_price = item.product.price

    return render(request, 'core/wishlist.html', {'wishlist_items': wishlist_items})
    
def remove_from_wishlist(request, wishlist_id):
    Wishlist.objects.filter(id=wishlist_id, user=request.user).delete()
    messages.success(request, "Item removed from wishlist!")
    return redirect('wishlist')

@login_required(login_url='login')
def cart_page(request):
    cart_items = Cart.objects.filter(user=request.user)
    # Discounted price calculate karna
    for item in cart_items:
        if item.product.discount:
            item.product.final_price = item.product.price - (item.product.price * item.product.discount / 100)
        else:
            item.product.final_price = item.product.price
    return render(request, 'core/cart.html', {'cart_items': cart_items})

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    selected_color = request.POST.get("selected_color", "")

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1, 'selected_color': selected_color}
    )

    if not created:
        cart_item.quantity += 1
        if selected_color:
            cart_item.selected_color = selected_color
        cart_item.save()

    # 🔥 Agar AJAX call hai to JSON response bhej do
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': '✅ Product added to cart!'})

    messages.success(request, "✅ Product added to cart!")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='login')
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id)
    cart_item.delete()
    messages.success(request, "✅ Item removed from cart!")
    return redirect('cart')
    
def help_center(request):
    return render(request, 'core/help_center.html')



# Admin Login Page
def admin_login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = ZeUser.objects.get(username=username)
        except ZeUser.DoesNotExist:
            messages.error(request, "Invalid credentials or not a superuser")
            return redirect('admin_login_page')

        if user.check_password(password) and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not a superuser")
            return redirect('admin_login_page')

    return render(request, 'admin_login.html')




# Admin Logout
@login_required(login_url='admin_login_page')
def admin_logout(request):
    logout(request)
    return redirect('home')


@login_required
def admin_dashboard(request):
    # Total Products
    total_products = ShopProduct.objects.count()

    # Total Orders
    total_orders = Order.objects.count()

    # Total Wishlist items
    total_wishlist = Wishlist.objects.count()

    # Total Cart items
    total_cart = Cart.objects.count()

    # Out of Stock Products (using quantity field)
    out_of_stock = ShopProduct.objects.filter(quantity__lte=0).count()

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_wishlist': total_wishlist,
        'total_cart': total_cart,
        'out_of_stock': out_of_stock,
    }

    return render(request, 'backend/dashboard.html', context)


def add_home_similar_product(request):
    product_names = ProductName.objects.all()
    colors = Color.COLOR_CHOICES  # tuple of tuples

    if request.method == 'POST':
        name = request.POST['name']
        price = float(request.POST['price'])
        discount = float(request.POST.get('discount', 0) or 0)
        section = 'other'
        image = request.FILES.get('image')
        product_id = int(request.POST.get('product'))  # Category id
        brand_id = int(request.POST.get('brand'))      # Brand id
        selected_colors = request.POST.getlist('colors')

        # ✅ Fetch proper instances
        product_category = get_object_or_404(ProductName, id=product_id)
        product_brand = get_object_or_404(BrandName, id=brand_id, product=product_category)
        quantity = int(request.POST.get('quantity', 1))  # default 1

        shop_product = ShopProduct.objects.create(
            name=name,
            product=product_category,
            brand=product_brand,
            price=price,
            discount=discount,
            section=section,
            colors=','.join(selected_colors),
            image=image,
            is_home_similar=True,  # mark as home similar
            quantity=quantity,

        )

        messages.success(request, "Product added successfully!")
        return redirect('add_home_similar_product')

    # show only home similar products
    products = ShopProduct.objects.filter(is_home_similar=True)

    return render(request, 'backend/add_home_similar_product.html', {
        'product_names': product_names,
        'colors': colors,
        'products': products
    })

    
# ----------- EDIT PRODUCT -----------
def edit_home_similar_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_names = ProductName.objects.all()
    brands = Brand.objects.all()
    colors = [(c.id, c.name, c.hex_code) for c in Color.objects.all()]

    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = float(request.POST['price'])
        product.discount = float(request.POST.get('discount', 0) or 0)
        product.section = request.POST.get('section', '')
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.category = ProductName.objects.get(id=request.POST['product'])
        product.brand = Brand.objects.get(id=request.POST['brand'])

        color_ids = request.POST.getlist('colors')
        if color_ids:
            product.colors.set(color_ids)
        else:
            product.colors.clear()

        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('add_home_similar_product')

    return render(request, 'backend/edit_home_similar_product.html', {
        'product': product,
        'product_names': product_names,
        'brands': brands,
        'colors': colors,
    })


# ----------- DELETE PRODUCT -----------
def delete_home_similar_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('add_home_similar_product')



    
# Edit ShopProduct
def edit_product(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)

    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.discount = request.POST.get('discount', 0)
        product.section = request.POST.get('section', 'other')
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('add_product')

    return render(request, 'backend/edit_product.html', {'product': product})

# Delete ShopProduct
def delete_product(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('add_product')


# Manage Product
@login_required
def manage_product(request):
    products = Product.objects.all()
    return render(request, 'backend/manage_product.html', {'products': products})


def add_banner(request):
    if request.method == "POST":
        image = request.FILES.get('image')
        title = request.POST.get('title', '')
        if image:
            Banner.objects.create(image=image, title=title, created_at=timezone.now())
        return redirect('add_banner')

    # Existing banners list (latest first)
    banners = Banner.objects.all().order_by('-created_at')
    return render(request, 'backend/add_banner.html', {'banners': banners})

def add_notice(request):
    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")
        image = request.FILES.get("image")

        Notice.objects.create(title=title, message=message, image=image)
        messages.success(request, "Notice added successfully!")
        return redirect("add_notice")

    notices = Notice.objects.all().order_by("-created_at")
    return render(request, "backend/add_notice.html", {"notices": notices})

# Edit Notice
def edit_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    if request.method == 'POST':
        notice.title = request.POST.get('title')
        notice.message = request.POST.get('message')
        if request.FILES.get('image'):
            notice.image = request.FILES['image']
        notice.save()
        messages.success(request, "Notice updated successfully!")
        return redirect('add_notice')

    return render(request, 'backend/edit_notice.html', {'notice': notice})


# Delete Notice
def delete_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, "Notice deleted successfully!")
    return redirect('add_notice')


def view_orders(request):
    orders = Order.objects.all()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')

    if start_date:
        orders = orders.filter(ordered_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(ordered_at__date__lte=end_date)

    if status == "pending":
        orders = orders.filter(order_confirmed=False, shipped=False, out_for_delivery=False, delivered_date__isnull=True)
    elif status == "confirmed":
        orders = orders.filter(order_confirmed=True)
    elif status == "shipped":
        orders = orders.filter(shipped=True)
    elif status == "out_for_delivery":
        orders = orders.filter(out_for_delivery=True)
    elif status == "delivered":
        orders = orders.filter(delivered_date__isnull=False)

    return render(request, 'backend/view_orders.html', {'orders': orders})


@login_required
def view_cart(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied")
        return redirect('home')

    cart_items = Cart.objects.all().order_by('-added_at')  # sab users ke cart items
    return render(request, "backend/view_cart.html", {"cart_items": cart_items})


def view_wishlist(request):
    wishlist_items = Wishlist.objects.all().select_related('user', 'product')
    return render(request, "backend/view_wishlist.html", {"wishlist_items": wishlist_items})



@csrf_exempt
def add_brand_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('Received data:', data)
            
            name = data.get('name', '').strip()
            category_id = data.get('category_id')
            print('Name:', name, 'Category ID:', category_id)

            if not category_id:
                return JsonResponse({'status':'error', 'message':'No category selected'})

            try:
                category = Category.objects.get(id=int(category_id))
            except (Category.DoesNotExist, ValueError) as e:
                print('Category error:', e)
                return JsonResponse({'status':'error', 'message':'Category not found'})

            if not name:
                return JsonResponse({'status':'error', 'message':'No brand name provided'})

            if Brand.objects.filter(name__iexact=name, category=category).exists():
                return JsonResponse({'status':'exists'})

            brand = Brand.objects.create(name=name, category=category)
            return JsonResponse({
                'status':'success',
                'id': brand.id,
                'name': brand.name,
                'category_name': category.name
            })

        except Exception as e:
            print('Error:', e)
            return JsonResponse({'status':'error', 'message':'Something went wrong'})


def get_brands(request, category_id):
    brands = Brand.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'brands': list(brands)})
@csrf_exempt
def edit_brand_ajax(request, brand_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        brand = Brand.objects.get(id=brand_id)
        brand.name = name
        brand.save()
        return JsonResponse({'status':'success', 'id': brand.id, 'name': brand.name, 'category_name': brand.category.name, 'category_id': brand.category.id})
    return JsonResponse({'status':'error'})

# Delete Brand
@csrf_exempt
def delete_brand_ajax(request, brand_id):
    if request.method == 'POST':
        brand = Brand.objects.get(id=brand_id)
        brand.delete()
        return JsonResponse({'status':'success'})
    return JsonResponse({'status':'error'})



def add_categories_products(request):
    db_categories = list(Category.objects.all())
    category_choices = [c[0] for c in Category._meta.get_field('name').choices]

    for choice in category_choices:
        if not any(c.name == choice for c in db_categories):
            db_categories.append(Category(name=choice))

    if request.method == 'POST':
        if 'category_submit' in request.POST:
            name = request.POST.get('category_name')
            if name:
                Category.objects.get_or_create(name=name)
                messages.success(request, f'Category "{name}" added successfully.')
            return redirect('add_categories_products')

        if 'product_submit' in request.POST:
            name = request.POST.get('product_name')
            price = request.POST.get('price')
            discount = request.POST.get('discount') or 0
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')
            image = request.FILES.get('image')

            category = get_object_or_404(Category, id=category_id)
            brand = Brand.objects.filter(id=brand_id).first() if brand_id else None

            # ---------------- Mobile fields ----------------
            ram = request.POST.get('ram')
            internal_storage = request.POST.get('internal_storage')
            battery = request.POST.get('battery')
            screen_size = request.POST.get('screen_size')
            os = request.POST.get('os')
            type_ = request.POST.get('type')
            primary_camera = request.POST.get('primary_camera')
            secondary_camera = request.POST.get('secondary_camera')

            # ---------------- Laptop fields ----------------
            processor = request.POST.get('processor')
            ram_capacity = request.POST.get('ram_capacity')
            ram_type = request.POST.get('ram_type')
            processor_generation = request.POST.get('processor_generation')
            ssd_capacity = request.POST.get('ssd_capacity')
            weight = request.POST.get('weight')
            touch_screen = request.POST.get('touch_screen')
            operating_system = request.POST.get('operating_system')
            quantity = request.POST['quantity']  # 👈 New line


            # ---------------- LED/OLED TV fields ----------------
            tv_operating_system = request.POST.get('tv_operating_system')
            smart_features = request.POST.getlist('smart_features')
            usb_ports = int(request.POST.get('usb_ports') or 0)
            hdmi_ports = int(request.POST.get('hdmi_ports') or 0)
            resolution = request.POST.get('resolution')
            refresh_rate = request.POST.get('refresh_rate')
            display_type = request.POST.get('display_type')
            tv_screen_size = request.POST.get('tv_screen_size')

            # ---------------- Soundbar fields ----------------
            wired_wireless = request.POST.get('wired_wireless')
            color_list = request.POST.getlist('color')
            color = ", ".join(color_list) if color_list else None

            # ---------------- Headphones specific ----------------
            compatible_with = request.POST.get('compatible_with')

            # ---------------- Camera specific fields ----------------
            felt_timer = request.POST.get('felt_timer')  # Yes/No

            # Multiple checkboxes
            mega_pixel_list = request.POST.getlist('mega_pixel')  # list
            mega_pixel = ", ".join(mega_pixel_list) if mega_pixel_list else None

            camera_color_list = request.POST.getlist('camera_color')
            camera_color = ", ".join(camera_color_list) if camera_color_list else None

            battery_list = request.POST.getlist('battery_type')
            battery_type = ", ".join(battery_list) if battery_list else None

            sensor_list = request.POST.getlist('sensor_type')
            ideal_for_list = request.POST.getlist('ideal_for')  # getlist for checkboxes

            sensor_type = ", ".join(sensor_list) if sensor_list else None
            wireless_speed_list = request.POST.getlist('wireless_speed')  # multiple checkboxes
            wireless_speed = ", ".join(wireless_speed_list) if wireless_speed_list else None

 
            # ---------------- Smartwatch fields ----------------
            dial_shape = request.POST.get('dial_shape')
            display_size = request.POST.get('display_size')
            ideal_for = ", ".join(ideal_for_list) if ideal_for_list else None


            color_names = request.POST.getlist('colors')
            print("Selected Colors:", color_names)
            color = ", ".join(color_names) if color_names else None

            
            product = Product.objects.create(
            name=name,
            price=price,
            discount=discount,
            category=category,
            brand=brand,
            image=image,

            # Mobile
            ram=ram,
            internal_storage=internal_storage,
            battery=battery,
            screen_size=screen_size,
            os=os,
            type=type_,
            primary_camera=primary_camera,
            secondary_camera=secondary_camera,

            # Laptop
            processor=processor,
            ram_capacity=ram_capacity,
            ram_type=ram_type,
            processor_generation=processor_generation,
            ssd_capacity=ssd_capacity,
            weight=weight,
            touch_screen=touch_screen,
            operating_system=operating_system,

            # LED/OLED TV
            tv_operating_system=tv_operating_system,
            smart_features=", ".join(smart_features) if smart_features else None,
            usb_ports=usb_ports,
            hdmi_ports=hdmi_ports,
            resolution=resolution,
            refresh_rate=refresh_rate,
            display_type=display_type,
            tv_screen_size=tv_screen_size,

            # Soundbar
            wired_wireless=wired_wireless,
                
            compatible_with=compatible_with,

            felt_timer=felt_timer,
            mega_pixel=mega_pixel,
            camera_color=camera_color,
            battery_type=battery_type,
            sensor_type=sensor_type,

            dial_shape=dial_shape,
            display_size=display_size,
            ideal_for=ideal_for,
            wireless_speed=wireless_speed,
            quantity=quantity,  # 👈 Save here

        )

        color_names = request.POST.getlist('colors')
        print("Selected Colors:", color_names)

        if color_names:
            for color_name in color_names:
                try:
                    color_obj = Color.objects.get(name=color_name)
                    product.colors.add(color_obj)
                except Color.DoesNotExist:
                    print(f"Color '{color_name}' not found in DB.")

            print("Colors added to product:", product.colors.all())

        messages.success(request, f'Product "{name}" added successfully.')
        return redirect('add_categories_products')
    wireless_speeds = ["0-15", "150-300", "300-450", "450-600", "600-750", "750-1000", "1000 above"]

    return render(request, 'backend/add_categories_products.html', {
        'categories': db_categories,
        'brands': Brand.objects.all(),
        'dial_shapes': Product.DIAL_SHAPE_CHOICES,      # model se fetch
        'ideal_for_options': Product.IDEAL_FOR_CHOICES,
        'wireless_speeds': wireless_speeds,
        'colors': Color.objects.all(),   # 👈 ye line important hai

        

        
    })




# Category-wise manage views (ForeignKey compatible)
def manage_mobile_products(request):
    products = Product.objects.filter(category__name='Mobile').prefetch_related('colors')
    return render(request, 'backend/mobile_products.html', {"products": products, "category_name": "Mobile"})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from core.models import Product, Brand, Category, Color

def edit_mobile_product(request, id):
    product = get_object_or_404(Product, id=id)
    colors = Color.objects.all()

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

        # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.ram = request.POST.get("ram")
        product.internal_storage = request.POST.get("internal_storage")
        product.battery = request.POST.get("battery")
        product.screen_size = request.POST.get("screen_size")
        product.os = request.POST.get("os")
        product.type = request.POST.get("type")
        product.primary_camera = request.POST.get("primary_camera")
        product.secondary_camera = request.POST.get("secondary_camera")

        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        # ✅ Handle colors (ManyToManyField)
        selected_colors = request.POST.getlist("color")  # list of color IDs as string
        product.save()  # save before setting M2M
        product.colors.set(selected_colors)  # replaces previous colors

        messages.success(request, "Product updated successfully! ✅")
        return redirect("manage_mobile_products")

    # GET request ke liye selected colors fetch karo
    selected_colors = product.colors.values_list('id', flat=True)  # list of color ids

    return render(request, "backend/edit_mobile_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": colors,
        "selected_colors": selected_colors,
    })



def delete_mobile_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Mobile Product deleted successfully!")
    return redirect("manage_mobile_products")


def manage_laptop_products(request):
    products = Product.objects.filter(category__name='Laptop')
    return render(request, 'backend/laptop_products.html', {"products": products, "category_name": "Laptop"})

# Edit Laptop Product
def edit_laptop_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

        # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)


        product.processor = request.POST.get("processor")
        product.ram_capacity = request.POST.get("ram_capacity")
        product.ram_type = request.POST.get("ram_type")
        product.screen_size = request.POST.get("screen_size")
        product.processor_generation = request.POST.get("processor_generation")
        product.ssd_capacity = request.POST.get("ssd_capacity")
        product.operating_system = request.POST.get("operating_system")
        product.weight = request.POST.get("weight")
        product.touch_screen = request.POST.get("touch_screen")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()

        # Colors update
        color_names = request.POST.getlist('colors')
        if color_names:
            product.colors.clear()
            for color_name in color_names:
                try:
                    color_obj = Color.objects.get(name=color_name)
                    product.colors.add(color_obj)
                except Color.DoesNotExist:
                    pass

        messages.success(request, "Laptop product updated successfully! ✅")
        return redirect("manage_laptop_products")

    # GET request
    return render(request, "backend/edit_laptop_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),
    })

# Delete Laptop Product
def delete_laptop_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Laptop product deleted successfully ❌")
    return redirect("manage_laptop_products")


def manage_tv_products(request):
    products = Product.objects.filter(category__name='LED/OLED TV')
    return render(request, 'backend/tv_products.html', {"products": products, "category_name": "LED/OLED TV"})

# Edit TV Product
def edit_tv_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")
         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.tv_screen_size = request.POST.get("tv_screen_size")
        product.resolution = request.POST.get("resolution")
        product.display_type = request.POST.get("display_type")
        product.smart_features = request.POST.get("smart_features")
        product.hdmi_ports = request.POST.get("hdmi_ports")
        product.usb_ports = request.POST.get("usb_ports")
        product.refresh_rate = request.POST.get("refresh_rate")
        product.tv_operating_system = request.POST.get("tv_operating_system")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()

        # Handle colors (assuming checkboxes with name="colors" in the form)
        color_ids = request.POST.getlist('colors')  # getlist because multiple checkboxes with same name
        # Clear existing colors and add new ones
        product.colors.clear()
        if color_ids:
            colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*colors)

        messages.success(request, "TV product updated successfully! ✅")
        return redirect("manage_tv_products")

    # GET request
    return render(request, "backend/edit_tv_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # pass colors for rendering in form
    })

# Delete TV Product
def delete_tv_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "TV product deleted successfully ❌")
    return redirect("manage_tv_products")

def manage_computer_hardware_products(request):
    products = Product.objects.filter(category__name='Computer Hardware').prefetch_related('colors')
    return render(request, 'backend/computer_hardware_products.html', {"products": products, "category_name": "Computer Hardware"})

def edit_hardware_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")
 # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        # Brand & Category update
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()

        # Colors update
        color_names = request.POST.getlist('colors')
        if color_names:
            product.colors.clear()  # pehle purane colors hatao
            for color_name in color_names:
                try:
                    color_obj = Color.objects.get(name=color_name)
                    product.colors.add(color_obj)
                except Color.DoesNotExist:
                    pass  # agar color nahi milta toh ignore karo

        messages.success(request, "Hardware product updated successfully! ✅")
        return redirect("manage_computer_hardware_products")

    # GET request mein saare colors bhejo, taaki form me dikha sako
    return render(request, "backend/edit_hardware_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # colors form me dikhane ke liye
    })

# Delete Hardware Product
def delete_hardware_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Hardware product deleted successfully ❌")
    return redirect("manage_hardware_products")


def manage_soundbar_products(request):
    products = Product.objects.filter(category__name='Soundbar')
    return render(request, 'backend/soundbar.html', {"products": products, "category_name": "Soundbar"})

# Edit Soundbar Product
def edit_soundbar_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.wired_wireless = request.POST.get("wired_wireless")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        # Handle colors (many-to-many)
        color_ids = request.POST.getlist('colors')
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Soundbar product updated successfully! ✅")
        return redirect("manage_soundbar_products")

    return render(request, "backend/edit_soundbar_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # Pass all colors to template
    })


# Delete Soundbar Product
def delete_soundbar_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Soundbar product deleted successfully ❌")
    return redirect("manage_soundbar_products")

def manage_speaker_products(request):
    products = Product.objects.filter(category__name='Speaker')
    return render(request, 'backend/speaker_products.html', {"products": products, "category_name": "Speaker"})

# Edit Speaker Product
def edit_speaker_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        
        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.category = Category.objects.get(id=category_id) if category_id else None

        # ✅ Handle Colors (Many-to-Many)
        color_ids = request.POST.getlist("colors")
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Speaker product updated successfully ✅")
        return redirect("manage_speaker_products")

    return render(request, "backend/edit_speaker_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # ✅ Pass colors to the template
    })


# Delete Speaker Product
def delete_speaker_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Speaker product deleted successfully ❌")
    return redirect("manage_speaker_products")

def manage_projector_products(request):
    products = Product.objects.filter(category__name='Projector')
    return render(request, 'backend/mprojector_products.html', {"products": products, "category_name": "Projector"})

def edit_projector_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)


        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle Colors (ManyToMany)
        color_ids = request.POST.getlist("colors")
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Projector product updated successfully!")
        return redirect("manage_projector_products")

    return render(request, "backend/edit_projector_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # Pass colors to template
    })


def delete_projector_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Projector product deleted successfully!")
    return redirect("manage_projector_products")

def manage_headphones_products(request):
    products = Product.objects.filter(category__name='Headphones')
    return render(request, 'backend/headphones_products.html', {"products": products, "category_name": "Headphones"})

# 2️⃣ Edit Headphones Product
def edit_headphones_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.compatible_with = request.POST.get("compatible_with")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle Colors (ManyToMany)
        color_ids = request.POST.getlist("colors")  # Note: plural 'colors'
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update (optional)
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Headphones product updated successfully!")
        return redirect("manage_headphones_products")

    return render(request, "backend/edit_headphones_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # Pass colors to template for checkbox list
    })

# 3️⃣ Delete Headphones Product
def delete_headphones_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Headphones product deleted successfully!")
    return redirect("manage_headphones_products")

def manage_camera_products(request):
    products = Product.objects.filter(category__name='Camera')
    return render(request, 'backend/camera_products.html', {"products": products, "category_name": "Camera"})

# Edit Camera Product
def edit_camera_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.felt_timer = request.POST.get("felt_timer")
        product.mega_pixel = request.POST.get("mega_pixel")
        product.battery_type = request.POST.get("battery_type")
        product.sensor_type = request.POST.get("sensor_type")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle multiple colors (assuming ManyToManyField 'colors')
        color_ids = request.POST.getlist("colors")  # note plural here!
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update (optional)
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Camera product updated successfully!")
        return redirect("manage_camera_products")

    return render(request, "backend/edit_camera_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # pass colors for checkbox list in template
    })

# Delete Camera Product
def delete_camera_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Camera product deleted successfully!")
    return redirect("manage_camera_products")

def manage_smartwatch_products(request):
    products = Product.objects.filter(category__name='Smartwatch')
    return render(request, 'backend/smartwatch_products.html', {"products": products, "category_name": "Smartwatch"})

# Edit Smartwatch Product
def edit_smartwatch_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.dial_shape = request.POST.get("dial_shape")
        product.display_size = request.POST.get("display_size")
        product.ideal_for = request.POST.get("ideal_for")

        # Brand & Category
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle colors (ManyToMany)
        color_ids = request.POST.getlist("colors")
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        # Image update (optional)
        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Smartwatch product updated successfully!")
        return redirect("manage_smartwatch_products")

    return render(request, "backend/edit_smartwatch_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # pass all colors for selection
    })

# Delete Smartwatch Product
def delete_smartwatch_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Smartwatch product deleted successfully!")
    return redirect("manage_smartwatch_products")

def manage_gaming_products(request):
    products = Product.objects.filter(category__name='Gaming')
    return render(request, 'backend/gaming_products.html', {"products": products, "category_name": "Gaming"})

# Edit Gaming Product
def edit_gaming_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        product.name = request.POST.get("name")  # changed to name for consistency
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        
        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle colors (ManyToMany)
        color_ids = request.POST.getlist("colors")
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)
        
        if "image" in request.FILES:
            product.image = request.FILES["image"]
        
        product.save()
        messages.success(request, "Gaming product updated successfully!")
        return redirect("manage_gaming_products")
    
    return render(request, "backend/edit_gaming_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # pass colors for the template
    })


# Delete Gaming Product
def delete_gaming_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Gaming product deleted successfully!")
    return redirect("manage_gaming_products")

def manage_wifi_router_products(request):
    products = Product.objects.filter(category__name='WiFi Router')
    return render(request, 'backend/wifi_products.html', {"products": products, "category_name": "Wi-Fi Router"})

# Edit Wi-Fi Router Product
def edit_wifi_router_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)

        product.wireless_speed = request.POST.get("wireless_speed")

        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle colors (ManyToMany)
        color_ids = request.POST.getlist("colors")  # note plural "colors"
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Wi-Fi Router product updated successfully!")
        return redirect("manage_wifi_router_products")

    return render(request, "backend/edit_wifi_router_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # pass colors for the template
    })

# Delete Wi-Fi Router Product
def delete_wifi_router_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Wi-Fi Router product deleted successfully!")
    return redirect("manage_wifi_router_products")

def manage_smart_home_products(request):
    products = Product.objects.filter(category__name='Smart Home Device')
    return render(request, 'backend/smarthome_products.html', {"products": products, "category_name": "Smart Home Devices"})

# Edit Smart Home Product
def edit_smart_home_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.product_name = request.POST.get("product_name")
        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount")

         # ✅ Added quantity field
        product.quantity = request.POST.get("quantity", 0)


        brand_id = request.POST.get("brand")
        category_id = request.POST.get("category")
        if brand_id:
            product.brand = Brand.objects.get(id=brand_id)
        if category_id:
            product.category = Category.objects.get(id=category_id)

        # Handle colors
        color_ids = request.POST.getlist("colors")  # plural 'colors'
        product.colors.clear()
        if color_ids:
            selected_colors = Color.objects.filter(id__in=color_ids)
            product.colors.add(*selected_colors)

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Smart Home product updated successfully!")
        return redirect("manage_smart_home_products")

    return render(request, "backend/edit_smart_home_product.html", {
        "product": product,
        "brands": Brand.objects.all(),
        "categories": Category.objects.all(),
        "colors": Color.objects.all(),  # Pass colors to template
    })

# Delete Smart Home Product
def delete_smart_home_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Smart Home product deleted successfully!")
    return redirect("manage_smart_home_products")
    
# All products view
def manage_all_products(request):
    products = Product.objects.all()
    return render(request, 'backend/manage_products.html', {"products": products, "category_name": "All Products"})



from django.shortcuts import render, redirect
from .models import ProductName, BrandName, ShopProduct

def add_product_and_brand(request):
    # Fetch existing products and brands
    product_names = ProductName.objects.all()
    brands = BrandName.objects.all()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')  # Check which form submitted

        # If Product Name form submitted
        if form_type == 'product_name':
            name = request.POST.get('product_name')
            if name:
                ProductName.objects.create(name=name)
                return redirect('add_product_and_brand')

        # If Brand form submitted
        elif form_type == 'brand':
            product_id = request.POST.get('product')
            brand_name = request.POST.get('brand_name')
            if product_id and brand_name:
                product = ProductName.objects.get(id=product_id)
                BrandName.objects.create(product=product, name=brand_name)
                return redirect('add_product_and_brand')

    context = {
        'product_names': product_names,
        'brands': brands
    }
    return render(request, 'backend/add_product_and_brand.html', context)


def edit_product_name(request, pk):
    product = get_object_or_404(ProductName, id=pk)
    if request.method == 'POST':
        new_name = request.POST.get('product_name')
        if new_name:
            product.name = new_name
            product.save()
            return redirect('add_product_and_brand')  # Combined page
    return render(request, 'backend/edit_product_name.html', {'product': product})

def edit_brand_name(request, pk):
    brand = get_object_or_404(BrandName, id=pk)
    products = ProductName.objects.all()
    if request.method == 'POST':
        new_name = request.POST.get('brand_name')
        product_id = request.POST.get('product')
        if new_name and product_id:
            brand.name = new_name
            brand.product = ProductName.objects.get(id=product_id)
            brand.save()
            return redirect('add_product_and_brand')
    return render(request, 'backend/edit_brand_name.html', {'brand': brand, 'products': products})


# Delete Product
def delete_product_name(request, pk):
    product = get_object_or_404(ProductName, id=pk)
    product.delete()
    return redirect('add_product_and_brand')

# Delete Brand
def delete_brand_name(request, pk):
    brand = get_object_or_404(BrandName, id=pk)
    brand.delete()
    return redirect('add_product_and_brand')
    
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages    
def add_shop_product(request):
    products = ProductName.objects.all()
    colors = Color.COLOR_CHOICES
    brands = BrandName.objects.all()

    if request.method == 'POST':
        shop_product_name = request.POST.get('shop_product_name')
        product_id = request.POST.get('product')
        brand_id = request.POST.get('brand')
        price = request.POST.get('price')
        discount = request.POST.get('discount') or 0
        quantity = request.POST.get('quantity')
        selected_colors = request.POST.getlist('colors')

        # Full details
        details_keys = request.POST.getlist('detail_keys')
        details_values = request.POST.getlist('detail_values')
        full_details_dict = {k: v for k, v in zip(details_keys, details_values) if k and v}

        # Specifications
        spec_keys = request.POST.getlist('spec_keys')
        spec_values = request.POST.getlist('spec_values')
        specifications_dict = {k: v for k, v in zip(spec_keys, spec_values) if k and v}

        # Descriptions
        desc_titles = request.POST.getlist('desc_titles')
        desc_texts = request.POST.getlist('desc_texts')
        desc_images = request.FILES.getlist('desc_images')

        # Main product image
        image = request.FILES.get('image')
        latest = request.POST.get('latest_launch') == 'on'
        best = request.POST.get('best_deal') == 'on'

        if shop_product_name and product_id and brand_id:
            product = ProductName.objects.get(id=product_id)
            brand = BrandName.objects.get(id=brand_id)
            color_str = ",".join(selected_colors)

            # Category-wise product limit check (15 max)
            category_product_count = ShopProduct.objects.filter(product=product).count()
            if category_product_count >= 15:
                messages.error(request, f"❌ Only 15 products allowed for '{product.name}' category.")
            else:
                # Save main ShopProduct
                shop_product = ShopProduct.objects.create(
                    name=shop_product_name,
                    product=product,
                    brand=brand,
                    price=float(price),
                    discount=float(discount),
                    quantity=int(quantity),
                    colors=color_str,
                    image=image,
                    full_details=full_details_dict,
                    specifications=specifications_dict,
                    latest_launch=latest,
                    best_deal=best
                )

                # Save descriptions separately
                for i in range(len(desc_titles)):
                    title = desc_titles[i]
                    text = desc_texts[i]
                    desc_image = desc_images[i] if i < len(desc_images) else None

                    if title or text or desc_image:
                        ShopProductDescription.objects.create(
                            shop_product=shop_product,
                            title=title,
                            text=text,
                            image=desc_image
                        )

                messages.success(request, f"✅ {shop_product_name} added successfully!")

        return render(request, 'backend/add_shop_product.html', {
            'products': products,
            'brands': brands,
            'colors': colors
        })

    # GET request
    return render(request, 'backend/add_shop_product.html', {
        'products': products,
        'brands': brands,
        'colors': colors
    })
          
def get_brands_by_product(request):
    product_id = request.GET.get('product_id')
    brands = []
    if product_id:
        brands_qs = BrandName.objects.filter(product_id=product_id)
        brands = [{'id': b.id, 'name': b.name} for b in brands_qs]
    return JsonResponse({'brands': brands})

def manage_shop_product(request):
    shop_products = ShopProduct.objects.all().order_by('quantity', '-id')
    all_products = Product.objects.all()
    all_brands = Brand.objects.all()

    # Filters from GET request
    date = request.GET.get('date')
    product_name = request.GET.get('product')  # ab name aa raha hai
    brand_name = request.GET.get('brand')      # ab name aa raha hai

    if date:
        shop_products = shop_products.filter(created_at__date=date)  # created_at field hona chahiye
    if product_name:
        shop_products = shop_products.filter(product__name__icontains=product_name)
    if brand_name:
        shop_products = shop_products.filter(brand__name__icontains=brand_name)

    # Prepare color list for each product
    for sp in shop_products:
        sp.color_list = sp.colors.split(',') if sp.colors else []

    context = {
        'shop_products': shop_products,
        'all_products': all_products,
        'all_brands': all_brands,
    }
    return render(request, 'backend/manage_shop_product.html', context)


def edit_shop_product(request, id):
    sp = ShopProduct.objects.get(id=id)
    products = ProductName.objects.all()
    brands = BrandName.objects.filter(product=sp.product)
    colors = Color.COLOR_CHOICES  # template me checkboxes ke liye

    if request.method == 'POST':
        sp.name = request.POST.get('shop_product_name')
        sp.product = ProductName.objects.get(id=request.POST.get('product'))
        sp.brand = BrandName.objects.get(id=request.POST.get('brand'))
        sp.price = request.POST.get('price')
        sp.discount = request.POST.get('discount') or 0
        sp.quantity = request.POST.get('quantity')

        # Colors
        selected_colors_post = request.POST.getlist('colors')
        sp.colors = ",".join(selected_colors_post)  # string me save

        # Image
        if 'image' in request.FILES:
            sp.image = request.FILES['image']

        sp.save()
        return redirect('manage_shop_product')

    # Existing selected colors ko list me convert for template
    selected_colors = sp.colors.split(',') if sp.colors else []

    return render(request, 'backend/edit_shop_product.html', {
        'shop_product': sp,
        'products': products,
        'brands': brands,
        'colors': colors,
        'selected_colors': selected_colors
    })




def delete_shop_product(request, id):
    sp = ShopProduct.objects.get(id=id)
    sp.delete()
    return redirect('manage_shop_product')

def toggle_visibility(request, pk, section):
    product = get_object_or_404(ShopProduct, pk=pk)

    if section == 'shop':
        product.show_in_shop = not product.show_in_shop
        messages.success(request, f"{product.name} {'added to' if product.show_in_shop else 'removed from'} Shop page.")
    elif section == 'latest':
        product.latest_launch = not product.latest_launch
        messages.success(request, f"{product.name} {'added to' if product.latest_launch else 'removed from'} Latest Launches.")
    elif section == 'deal':
        product.best_deal = not product.best_deal
        messages.success(request, f"{product.name} {'added to' if product.best_deal else 'removed from'} Best Deals.")

    product.save()
    return redirect('manage_shop_product')




def add_full_details(request):
    categories = ProductName.objects.all()  # Category dropdown

    if request.method == 'POST':
        product_id = request.POST.get('shop_product')
        full_details_json = request.POST.get('full_details')

        # Product instance fetch karna
        product = get_object_or_404(ShopProduct, id=product_id)

        # JSON parse karke save karna
        if full_details_json:
            try:
                product.full_details = json.loads(full_details_json)
                product.save()
                messages.success(request, "✅ Full details saved successfully!")
            except json.JSONDecodeError:
                messages.error(request, "❌ Invalid details format!")

    return render(request, 'backend/add_full_details.html', {'categories': categories})


# AJAX: Get shop products based on selected category
def get_shop_products(request):
    category_id = request.GET.get('category_id')
    
    if category_id:
        # category_id se related ShopProduct instances fetch karein
        shop_products = ShopProduct.objects.filter(product_id=category_id)
        data = [{'id': sp.id, 'name': sp.name} for sp in shop_products]
    else:
        data = []

    return JsonResponse({'shop_products': data})


def manage_full_details(request):
    # Show all products with full_details
    products = ShopProduct.objects.exclude(full_details={})
    return render(request, 'backend/manage_full_details.html', {'products': products})

def edit_full_detail(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    if request.method == 'POST':
        full_details_json = request.POST.get('full_details')
        product.full_details = json.loads(full_details_json)
        product.save()
        messages.success(request, f"✅ Full details updated for {product.name}")
        return redirect('manage_full_details')
    return render(request, 'backend/edit_full_detail.html', {'product': product})

def delete_full_detail(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)
    product.full_details = {}
    product.save()
    messages.success(request, f"❌ Full details deleted for {product.name}")
    return redirect('manage_full_details')

def details_product(request, product_id):
    product = get_object_or_404(ShopProduct, id=product_id)

    # Already ordered quantity
    ordered_qty = Order.objects.filter(
        product=product,
        status__in=['Pending', 'Shipped']
    ).aggregate(total=models.Sum('quantity'))['total'] or 0

    available_quantity = product.quantity - ordered_qty
    color_list = product.colors.split(',') if product.colors else []

    # Discounted price
    discounted_price = product.price
    if product.discount:
        discounted_price = product.price * (100 - product.discount) / 100

    # Average rating
    avg_rating = Order.objects.filter(product=product, rating__isnull=False).aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating or 0, 1)

    # Total ratings & reviews (reviews counted as orders with rating)
    total_ratings = Order.objects.filter(product=product, rating__isnull=False).count()
    total_reviews = total_ratings  # kyunki comment field nahi hai

    context = {
        'product': product,
        'available_quantity': available_quantity,
        'color_list': color_list,
        'discounted_price': discounted_price,
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
        'total_reviews': total_reviews,
    }

    return render(request, 'core/details_product.html', context)

def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Reduce stock if order confirmed and not reduced yet
    if order.order_confirmed and not order.stock_reduced:
        product = order.product
        if product.quantity >= order.quantity:
            product.quantity -= order.quantity
            product.save()
        order.stock_reduced = True
        order.save()

    # Timeline steps
    steps = [
        {'name': 'Order Confirmed', 'status': order.order_confirmed, 'date': order.ordered_at},
        {'name': 'Shipped', 'status': order.shipped, 'date': order.shipped_at},
        {'name': 'Out for Delivery', 'status': order.out_for_delivery, 'date': order.out_for_delivery_at},
        {'name': 'Delivered', 'status': order.delivered_date, 'date': order.delivered_date},
    ]

    reasons = [
        "Product damaged",
        "Wrong item received",
        "Item not as described",
        "Late delivery",
        "Quality not satisfactory",
        "Other issue"
    ]
    
    return render(request, 'core/order_details.html', {
        'order': order,
        'steps': steps,
        'reasons': reasons
    })


def save_order_rating(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        rating = request.POST.get("rating")
        if rating:
            order.rating = float(rating)
            order.save()
            # Agar AJAX use kar rahe ho to JsonResponse bhej sakte
            # return JsonResponse({"success": True, "message": "Rating saved!"})
        return redirect('details_product', product_id=order.product.id)


def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "POST":
        # Example checkboxes from form
        order_confirmed = request.POST.get('order_confirmed') == 'on'
        shipped = request.POST.get('shipped') == 'on'
        out_for_delivery = request.POST.get('out_for_delivery') == 'on'
        delivered_date = request.POST.get('delivered_date')  # YYYY-MM-DD

        # Update fields
        order.order_confirmed = order_confirmed
        if shipped and not order.shipped_at:
            order.shipped_at = timezone.now()
        order.shipped = shipped

        if out_for_delivery and not order.out_for_delivery_at:
            order.out_for_delivery_at = timezone.now()
        order.out_for_delivery = out_for_delivery

        if delivered_date:
            order.delivered_date = delivered_date

        order.save()
        messages.success(request, f"Order {order.id} status updated successfully.")
        return redirect('view_orders')  # jaha se admin orders dekh raha tha

    return redirect('view_orders')


from django.utils.dateparse import parse_datetime

def order_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    data = {
        "order_confirmed": order.order_confirmed,
        "order_confirmed_at": order.ordered_at.isoformat() if order.order_confirmed else None,
        "shipped": order.shipped,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "out_for_delivery": order.out_for_delivery,
        "out_for_delivery_at": order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
        "delivered_date": order.delivered_date.isoformat() if order.delivered_date else None,
    }
    return JsonResponse(data)
