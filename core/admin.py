from django.contrib import admin

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'total_price', 'ordered_at', 'shipping_address')
    list_filter = ('ordered_at',)
    search_fields = ('user__email', 'product__name', 'shipping_address__name')