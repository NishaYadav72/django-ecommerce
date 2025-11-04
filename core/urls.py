from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name="home"),
    path('shop/', views.shop_page, name='shop_page'),      # Shop main page

    path('login/', views.login_view, name='login'),
    path("signup/", views.signup_view, name="signup"),
    path('category/<int:product_id>/', views.category_details, name='category_details'),
    path("search/", views.search_products, name="search_products"),


# Category URLs
    path('category/mobile/', views.mobile_products, name='mobile_products'),
    path('category/computer-hardware/', views.computer_hardware_products, name='computer_hardware_products'),
    path('category/tv/', views.tv_products, name='tv_products'),
    path('category/soundbar/', views.soundbar_products, name='soundbar_products'),
    path('category/speaker/', views.speaker_products, name='speaker_products'),
    path('category/laptop/', views.laptop_products, name='laptop_products'),
    path('category/projector/', views.projector_products, name='projector_products'),
    path('category/headphones/', views.headphones_products, name='headphones_products'),
    path('category/camera/', views.camera_products, name='camera_products'),
    path('category/smartwatch/', views.smartwatch_products, name='smartwatch_products'),
    path('category/gaming/', views.gaming_products, name='gaming_products'),
    path('category/wi-fi-router/', views.wifi_router_products, name='wifi_router_products'),
    path('category/smart-home-devices/', views.smart_home_devices_products, name='smart_home_devices_products'),


    path('inline-password-reset/', views.inline_password_reset, name='inline_password_reset'),
    path('dashboard/', views.dashboard, name='dashboard'),
path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    path('cart/', views.cart_page, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path("orders/", views.orders, name="orders"),  # ✅ yeh line add karein
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('save-address/<int:product_id>/', views.save_address, name='save_address'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('checkout-payment/<int:product_id>/', views.checkout_payment, name='checkout_payment'),
    path("update-cart-quantity/<int:product_id>/", views.update_cart_quantity, name="update_cart_quantity"),
    path('delete-address/', views.delete_address, name='delete_address'),
    path('set-delivery-address/', views.set_delivery_address, name='set_delivery_address'),
    path('payment/<int:product_id>/', views.payment_view, name='payment'),


path('return/<int:order_id>/', views.return_request, name='return_request'),
    path('return/confirm/<int:order_id>/', views.return_confirm, name='return_confirm'),
    path('process_return/<int:order_id>/', views.process_return, name='process_return'),

    path('help-center/', views.help_center, name='help_center'),
    path('order/<int:order_id>/save_rating/', views.save_order_rating, name='save_order_rating'),


#******************************************BACKEND****************************************************************



  
path('add-product-brand/', views.add_product_and_brand, name='add_product_and_brand'),
path('edit-product/<int:pk>/', views.edit_product_name, name='edit_product_name'),
path('edit-brand/<int:pk>/', views.edit_brand_name, name='edit_brand_name'),
path('delete-product/<int:pk>/', views.delete_product_name, name='delete_product_name'),
path('delete-brand/<int:pk>/', views.delete_brand_name, name='delete_brand_name'),


path('add-shop-product/', views.add_shop_product, name='add_shop_product'),
path('get-brands/', views.get_brands_by_product, name='get_brands_by_product'),
path('manage-shop-product/', views.manage_shop_product, name='manage_shop_product'),
 # Edit & Delete URLs
    path('edit-shop-product/<int:id>/', views.edit_shop_product, name='edit_shop_product'),
    path('delete-shop-product/<int:id>/', views.delete_shop_product, name='delete_shop_product'),
    




    path('admin-login/', views.admin_login_page, name='admin_login_page'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('add-product/', views.add_home_similar_product, name='add_home_similar_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),

    path('edit-home-similar-product/<int:product_id>/', views.edit_home_similar_product, name='edit_home_similar_product'),
    path('delete-home-similar-product/<int:product_id>/', views.delete_home_similar_product, name='delete_home_similar_product'),

    
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),

    path('manage-product/', views.manage_product, name='manage_product'),
    path('add-banner/', views.add_banner, name='add_banner'),
    path('add-notice/', views.add_notice, name='add_notice'),
    path('edit-notice/<int:pk>/', views.edit_notice, name='edit_notice'),
    path('delete-notice/<int:pk>/', views.delete_notice, name='delete_notice'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('view_wishlist/', views.view_wishlist, name='view_wishlist'),
    path('add_categories_products/', views.add_categories_products, name='add_categories_products'),
    
    path('ajax/add_brand/', views.add_brand_ajax, name='add_brand_ajax'),
    path('ajax/get_brands/<int:category_id>/', views.get_brands, name='get_brands'),
    path('ajax/edit_brand/<int:brand_id>/', views.edit_brand_ajax, name='edit_brand_ajax'),
    path('ajax/delete_brand/<int:brand_id>/', views.delete_brand_ajax, name='delete_brand_ajax'),


 # Manage Categories & Products URLs
    path('manage/mobile/', views.manage_mobile_products, name='manage_mobile_products'),
    path("edit-mobile-product/<int:id>/", views.edit_mobile_product, name="edit_mobile_product"),
    path("delete-mobile-product/<int:id>/", views.delete_mobile_product, name="delete_mobile_product"),

    path('manage/laptop/', views.manage_laptop_products, name='manage_laptop_products'),
    path("edit-laptop-product/<int:id>/", views.edit_laptop_product, name="edit_laptop_product"),
    path("delete-laptop-product/<int:id>/", views.delete_laptop_product, name="delete_laptop_product"),

    path('manage/tv/', views.manage_tv_products, name='manage_tv_products'),
    path("edit-tv-product/<int:id>/", views.edit_tv_product, name="edit_tv_product"),
    path("delete-tv-product/<int:id>/", views.delete_tv_product, name="delete_tv_product"),

    path('manage/computer-hardware/', views.manage_computer_hardware_products, name='manage_computer_hardware_products'),
    path("edit-hardware-product/<int:id>/", views.edit_hardware_product, name="edit_hardware_product"),
    path("delete-hardware-product/<int:id>/", views.delete_hardware_product, name="delete_hardware_product"),

    path('manage/soundbar/', views.manage_soundbar_products, name='manage_soundbar_products'),
    path("edit-soundbar-product/<int:id>/", views.edit_soundbar_product, name="edit_soundbar_product"),
    path("delete-soundbar-product/<int:id>/", views.delete_soundbar_product, name="delete_soundbar_product"),

    path('manage/speaker/', views.manage_speaker_products, name='manage_speaker_products'),
    path("edit-speaker-product/<int:id>/", views.edit_speaker_product, name="edit_speaker_product"),
    path("delete-speaker-product/<int:id>/", views.delete_speaker_product, name="delete_speaker_product"),

    path('manage/projector/', views.manage_projector_products, name='manage_projector_products'),
    path("edit-projector-product/<int:product_id>/", views.edit_projector_product, name="edit_projector_product"),
    path("delete-projector-product/<int:product_id>/", views.delete_projector_product, name="delete_projector_product"),

    path('manage/headphones/', views.manage_headphones_products, name='manage_headphones_products'),
    path("edit-headphones-product/<int:product_id>/", views.edit_headphones_product, name="edit_headphones_product"),
    path("delete-headphones-product/<int:product_id>/", views.delete_headphones_product, name="delete_headphones_product"),

    path('manage/camera/', views.manage_camera_products, name='manage_camera_products'),
    path("edit-camera-product/<int:product_id>/", views.edit_camera_product, name="edit_camera_product"),
    path("delete-camera-product/<int:product_id>/", views.delete_camera_product, name="delete_camera_product"),

    path('manage/smartwatch/', views.manage_smartwatch_products, name='manage_smartwatch_products'),
    path("edit-smartwatch-product/<int:product_id>/", views.edit_smartwatch_product, name="edit_smartwatch_product"),
    path("delete-smartwatch-product/<int:product_id>/", views.delete_smartwatch_product, name="delete_smartwatch_product"),

    path('manage/gaming/', views.manage_gaming_products, name='manage_gaming_products'),
    path("edit-gaming-product/<int:product_id>/", views.edit_gaming_product, name="edit_gaming_product"),
    path("delete-gaming-product/<int:product_id>/", views.delete_gaming_product, name="delete_gaming_product"),

    path('manage/wi-fi-router/', views.manage_wifi_router_products, name='manage_wifi_router_products'),
    path("edit-wifi-router-product/<int:product_id>/", views.edit_wifi_router_product, name="edit_wifi_router_product"),
    path("delete-wifi-router-product/<int:product_id>/", views.delete_wifi_router_product, name="delete_wifi_router_product"),

    path('manage/smart-home-devices/', views.manage_smart_home_products, name='manage_smart_home_products'),
    path("edit-smart-home-product/<int:product_id>/", views.edit_smart_home_product, name="edit_smart_home_product"),
    path("delete-smart-home-product/<int:product_id>/", views.delete_smart_home_product, name="delete_smart_home_product"),

    path('manage/all/', views.manage_all_products, name='manage_all_products'),


   




# urls.py
path('add-full-details/', views.add_full_details, name='add_full_details'),

path('manage_full_details/', views.manage_full_details, name='manage_full_details'),
path('edit_full_detail/<int:product_id>/', views.edit_full_detail, name='edit_full_detail'),
path('delete_full_detail/<int:product_id>/', views.delete_full_detail, name='delete_full_detail'),
    path('get-shop-products/', views.get_shop_products, name='get_shop_products'),
    path('product/<int:product_id>/', views.details_product, name='details_product'),


    path('order/<int:order_id>/', views.order_details, name='order_details'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('api/order_status/<int:order_id>/', views.order_status_api, name='order_status_api'),

 path('toggle_visibility/<int:pk>/<str:section>/', views.toggle_visibility, name='toggle_visibility'),
    
]
