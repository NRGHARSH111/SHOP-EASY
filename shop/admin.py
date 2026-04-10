from django.contrib import admin
from django.utils.html import format_html
from .models import Product, CartItem, Order, OrderItem

# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'price', 'sale_price', 'display_image', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description', 'category']
    list_editable = ['price', 'sale_price']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price'),
            'description': 'Set sale_price to offer a discount'
        }),
        ('Media', {
            'fields': ('image_url',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_image(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', obj.image_url)
        return "No Image"
    display_image.short_description = 'Preview'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity', 'subtotal']
    fields = ['product', 'product_name', 'price', 'quantity', 'subtotal']
    
    def subtotal(self, obj):
        return f"₹{obj.price * obj.quantity:.2f}"
    subtotal.short_description = 'Subtotal'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_price_display', 'status', 'item_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'id']
    readonly_fields = ['created_at', 'user', 'total_price', 'order_details']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Financial Details', {
            'fields': ('total_price', 'total_price_display'),
        }),
        ('Order Details', {
            'fields': ('order_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def order_number(self, obj):
        return format_html('<strong>#ORD-{}</strong>', obj.id)
    order_number.short_description = 'Order #'
    
    def total_price_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #2e7d32;">₹{:.2f}</span>', obj.total_price)
    total_price_display.short_description = 'Total Amount'
    
    def item_count(self, obj):
        count = obj.items.count()
        return format_html('{} item{}', count, 's' if count != 1 else '')
    item_count.short_description = 'Items'
    
    def order_details(self, obj):
        items = obj.items.all()
        if not items:
            return "No items in this order"
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #f5f5f5;'><th style='padding: 8px; border: 1px solid #ddd;'>Product</th><th style='padding: 8px; border: 1px solid #ddd;'>Price</th><th style='padding: 8px; border: 1px solid #ddd;'>Qty</th><th style='padding: 8px; border: 1px solid #ddd;'>Subtotal</th></tr>"
        
        for item in items:
            subtotal = item.price * item.quantity
            html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{item.product_name}</td><td style='padding: 8px; border: 1px solid #ddd;'>₹{item.price:.2f}</td><td style='padding: 8px; border: 1px solid #ddd;'>{item.quantity}</td><td style='padding: 8px; border: 1px solid #ddd;'>₹{subtotal:.2f}</td></tr>"
        
        html += "</table>"
        return format_html(html)
    order_details.short_description = 'Order Items Summary'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'added_at', 'subtotal']
    list_filter = ['added_at', 'product__category']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['added_at', 'subtotal']
    
    def subtotal(self, obj):
        price = obj.product.sale_price if obj.product.sale_price else obj.product.price
        return f"₹{price * obj.quantity:.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'product_name', 'price', 'quantity', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['product_name', 'order__user__username']
    readonly_fields = ['subtotal']
    
    def subtotal(self, obj):
        return f"₹{obj.price * obj.quantity:.2f}"
    subtotal.short_description = 'Subtotal'


# Admin site configuration
admin.site.site_header = "ShopEasy Administration"
admin.site.site_title = "ShopEasy Admin Portal"
admin.site.index_title = "Welcome to ShopEasy Admin"
