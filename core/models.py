from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model  
from django.conf import settings  
from datetime import datetime

#*******************************************USER**********************************************************
class ZeUser(AbstractUser):
    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

#*******************************************BACKEND**********************************************************

class ProductName(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class BrandName(models.Model):
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ShopProduct(models.Model):
    name = models.CharField(max_length=255)
    product = models.ForeignKey(ProductName, on_delete=models.CASCADE)
    brand = models.ForeignKey(BrandName, on_delete=models.CASCADE)
    price = models.FloatField()
    discount = models.FloatField(default=0)
    quantity = models.IntegerField()
    colors = models.CharField(max_length=255, blank=True)  # comma-separated color names
    image = models.ImageField(upload_to='shop_products/', null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)  # RAM, warranty, etc.
    full_details = models.JSONField(default=dict, blank=True)  # ✅ Extra content
    specifications = models.JSONField(default=dict, blank=True)  # ✅ new specs
    latest_launch = models.BooleanField(default=False)
    best_deal = models.BooleanField(default=False)
    show_in_shop = models.BooleanField(default=True)
    is_home_similar = models.BooleanField(default=False)

    section = models.CharField(
        max_length=20,
        choices=(
            ('latest', 'Latest Launches'),
            ('deals', 'Best Deals'),
            ('other', 'Other'),
        ),
        default='other'
    )
    def color_list(self):
        # template me use karne ke liye list me convert
        return self.colors.split(',') if self.colors else []

    def __str__(self):
        return self.name

class ShopProductDescription(models.Model):
    shop_product = models.ForeignKey('ShopProduct', on_delete=models.CASCADE, related_name='descriptions')
    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='shop_product/descriptions/', blank=True, null=True)



from django.db import models

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('Mobile', 'Mobile'),
        ('LED/OLED TV', 'LED/OLED TV'),
        ('Computer Hardware', 'Computer Hardware'),
        ('Soundbar', 'Soundbar'),
        ('Speaker', 'Speaker'),
        ('Laptop', 'Laptop'),
        ('Projector', 'Projector'),
        ('Headphones', 'Headphones'),
        ('Camera', 'Camera'),
        ('Smartwatch', 'Smartwatch'),
        ('Gaming', 'Gaming'),
        ('WiFi Router', 'WiFi Router'),
        ('Smart Home Device', 'Smart Home Device'),
    ]

    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='brands')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


User = get_user_model()

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.FloatField()
    discount = models.FloatField(default=0)

    section = models.CharField(
        max_length=20,
        choices=(
            ('latest', 'Latest Launches'),
            ('deals', 'Best Deals'),
            ('other', 'Other'),
        ),
        default='other'
    )
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # ---------------- Mobile-specific fields ----------------
    ram = models.CharField(max_length=50, blank=True, null=True)
    internal_storage = models.CharField(max_length=50, blank=True, null=True)
    battery = models.CharField(max_length=50, blank=True, null=True)
    screen_size = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    primary_camera = models.CharField(max_length=50, blank=True, null=True)
    secondary_camera = models.CharField(max_length=50, blank=True, null=True)

    # ---------------- Laptop-specific fields ----------------
    processor = models.CharField(max_length=255, blank=True, null=True)
    ram_capacity = models.CharField(max_length=50, blank=True, null=True)
    ram_type = models.CharField(max_length=50, blank=True, null=True)
    processor_generation = models.CharField(max_length=50, blank=True, null=True)
    ssd_capacity = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    touch_screen = models.CharField(max_length=10, blank=True, null=True)
    operating_system = models.CharField(max_length=50, blank=True, null=True)

    # ---------------- LED/OLED TV-specific fields ----------------
    tv_operating_system = models.CharField(max_length=100, blank=True, null=True)
    smart_features = models.CharField(max_length=255, blank=True, null=True)  # WiFi, Bluetooth etc.
    usb_ports = models.IntegerField(blank=True, null=True)
    hdmi_ports = models.IntegerField(blank=True, null=True)
    resolution = models.CharField(max_length=100, blank=True, null=True)
    refresh_rate = models.CharField(max_length=50, blank=True, null=True)
    display_type = models.CharField(max_length=100, blank=True, null=True)  # LED / OLED / QLED etc.
    tv_screen_size = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)  # 👈 New field added

    # ---------------- soundbar-specific fields ----------------
    wired_wireless = models.CharField(max_length=50, blank=True, null=True)
    colors = models.ManyToManyField('Color', blank=True)
 


    # ---------------- Common ----------------
    created_at = models.DateTimeField(auto_now_add=True)
    compatible_with = models.CharField(max_length=200, null=True, blank=True)
 # camera -----------------------------------------------------------
    felt_timer = models.CharField(max_length=3, choices=[('Yes','Yes'),('No','No')], null=True, blank=True)
    
    MEGA_PIXEL_CHOICES = [
        ('Below 6MP', 'Below 6MP'),
        ('6 to 7.9MP', '6 to 7.9MP'),
        ('8 to 9.9MP', '8 to 9.9MP'),
        ('10 to 13.99MP', '10 to 13.99MP'),
        ('14 to 15.99MP', '14 to 15.99MP'),
        ('18 to 23.99MP', '18 to 23.99MP'),
        ('24MP & above', '24MP & above'),
    ]
    mega_pixel = models.CharField(max_length=20, null=True, blank=True)  # Multiple choice: comma separated

    CAMERA_COLOR_CHOICES = [
        ('Black','Black'), ('White','White'), ('Red','Red'), ('Blue','Blue')
    ]
    camera_color = models.CharField(max_length=50, null=True, blank=True)  # Multiple choice: comma separated

    BATTERY_CHOICES = [
        ('AA Battery','AA Battery'), 
        ('AA Rechargeable Battery','AA Rechargeable Battery'),
        ('AAA Battery','AAA Battery'),
        ('AAA Rechargeable Battery','AAA Rechargeable Battery'),
        ('Lithium Battery','Lithium Battery'),
    ]
    battery_type = models.CharField(max_length=50, null=True, blank=True)  # Multiple choice: comma separated

    SENSOR_CHOICES = [
        ('BSICMOS','BSICMOS'),
        ('CCD','CCD'),
        ('CMOS','CMOS'),
        ('MOS','MOS'),
        ('NMOS','NMOS'),
    ]
    sensor_type = models.CharField(max_length=50, null=True, blank=True)  # Multiple choice: comma separated


 # Smartwatch specific fields
    DIAL_SHAPE_CHOICES = [
        ('Contemporary', 'Contemporary'),
        ('Curved', 'Curved'),
        ('Oval', 'Oval'),
        ('Rectangle', 'Rectangle'),
        ('Round', 'Round'),
        ('Square', 'Square'),
        ('Tonneau', 'Tonneau'),
    ]
    dial_shape = models.CharField(max_length=20, choices=DIAL_SHAPE_CHOICES, null=True, blank=True)
    display_size = models.CharField(max_length=50, null=True, blank=True)
    IDEAL_FOR_CHOICES = [
        ('Kids', 'Kids'),
        ('Men', 'Men'),
        ('Women', 'Women'),
        ('Unisex', 'Unisex'),
    ]
    ideal_for = models.CharField(max_length=20, choices=IDEAL_FOR_CHOICES, null=True, blank=True)
    wireless_speed = models.CharField(max_length=100, null=True, blank=True)  # Multiple speeds comma-separated


    def __str__(self):
        return self.name



class Color(models.Model):
    COLOR_CHOICES = [
        ('Red', '#FF0000'),
        ('Blue', '#0000FF'),
        ('Green', '#008000'),
        ('Black', '#000000'),
        ('White', '#FFFFFF'),
        ('Yellow', '#FFFF00'),
        ('Orange', '#FFA500'),
        ('Pink', '#FFC0CB'),
        ('Purple', '#800080'),
        ('Brown', '#A52A2A'),
        ('Gray', '#808080'),
        ('Cyan', '#00FFFF'),
        ('Magenta', '#FF00FF'),
        # Tum aur colors add kar sakte ho
    ]

    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, default="#000000")  # preview ke liye

    def __str__(self):
        return self.name

    @classmethod
    def populate_colors(cls):
        """Ye method use karke saare colors database me add kar sakte ho"""
        for name, hex_code in cls.COLOR_CHOICES:
            cls.objects.get_or_create(name=name, hex_code=hex_code)


class ProductDetails(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    colors = models.ManyToManyField(Color, blank=True)  # multiple colors possible
    specifications = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    warranty = models.CharField(max_length=100, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product_details/', blank=True, null=True)

    def __str__(self):
        return self.product.name

# Ab user ko get_user_model se leke Wishlist define karo
from django.contrib.auth import get_user_model
User = get_user_model()

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('ShopProduct', on_delete=models.CASCADE)  # Product -> ShopProduct

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('ShopProduct', on_delete=models.CASCADE)  # yaha change kiya
    quantity = models.PositiveIntegerField(default=1)
    selected_color = models.CharField(max_length=50, blank=True, null=True)

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.product.name} ({self.quantity})"

    @property
    def total_price(self):
        if self.product.discount:  # agar discount hai to use
            discounted_price = self.product.price - (self.product.price * self.product.discount / 100)
            return discounted_price * self.quantity
        return self.product.price * self.quantity

        
class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='banners/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title or "Banner"

class Notice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    image = models.ImageField(upload_to='notices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    alt_mobile = models.CharField(max_length=15, blank=True, null=True)
    pincode = models.CharField(max_length=10)
    locality = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    is_delivery = models.BooleanField(default=False)  # <-- ye field must


    def __str__(self):
        return f"{self.name} - {self.city}"

from django.db import models
from django.conf import settings

class Order(models.Model):
    PAYMENT_CHOICES = (
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('emi', 'EMI'),
        ('netbanking', 'Net Banking'),
        ('cod', 'Cash on Delivery'),
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    RETURN_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('ShopProduct', on_delete=models.CASCADE)
    shipping_address = models.ForeignKey('ShippingAddress', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.FloatField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    ordered_at = models.DateTimeField(auto_now_add=True)
    
    order_confirmed = models.BooleanField(default=False)
    shipped = models.BooleanField(default=False)
    out_for_delivery = models.BooleanField(default=False)
    delivered_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)  # <--- rating field

    shipped_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)

    # Return-related fields
    return_requested = models.BooleanField(default=False)
    return_reason = models.CharField(max_length=255, blank=True, null=True)
    return_comment = models.TextField(blank=True, null=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='pending')
    return_expected_date = models.DateField(blank=True, null=True)
    stock_reduced = models.BooleanField(default=False)  # quantity already reduced or not

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"
