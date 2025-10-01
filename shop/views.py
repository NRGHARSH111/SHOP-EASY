from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.

# Hardcoded product catalog
PRODUCTS = [
    {"id": 1, "name": "Wireless Mouse", "price": 19.99, "imageUrl": "https://images.unsplash.com/photo-1660491083562-d91a64d6ea9c?q=80&w=881&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Accessories"},
    {"id": 2, "name": "Mechanical Keyboard", "price": 49.99, "imageUrl": "https://images.unsplash.com/photo-1602025882379-e01cf08baa51?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Accessories", "salePrice": 39.99},
    {"id": 3, "name": "USB-C Hub", "price": 29.99, "imageUrl": "https://images.unsplash.com/photo-1572721546624-05bf65ad7679?q=80&w=1073&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Accessories"},
    {"id": 4, "name": "Noise-Canceling Headphones", "price": 89.99, "imageUrl": "https://plus.unsplash.com/premium_photo-1680346529160-549ad950bd1f?q=80&w=1074&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Audio", "salePrice": 74.99},
    {"id": 5, "name": "Webcam 1080p", "price": 39.99, "imageUrl": "https://images.unsplash.com/photo-1623949556303-b0d17d198863?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Video"},
    {"id": 6, "name": "Portable SSD 1TB", "price": 109.99, "imageUrl": "https://images.unsplash.com/photo-1657731739866-d3971e421622?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Storage"},
    {"id": 7, "name": "Laptop Stand", "price": 24.99, "imageUrl": "https://images.unsplash.com/photo-1623251609314-97cc1f84e3ed?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "Accessories"},
    {"id": 8, "name": "Bluetooth Speaker", "price": 34.99, "imageUrl": "https://images.unsplash.com/photo-1582978571763-2d039e56f0c3?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Nnx8Qmx1ZXRvb3RoJTIwU3BlYWtlcnxlbnwwfHwwfHx8MA%3D%3D", "category": "Audio", "salePrice": 29.99},
    {"id": 9, "name": "Men NA Solid Suit", "price": 500.99, "imageUrl": "https://images.unsplash.com/photo-1621335829175-95f437384d7c?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "clothing", "salePrice": 1000.99},
    {"id": 10, "name": "Men & Women Casual Jacket", "price": 800.99, "imageUrl": "https://images.unsplash.com/photo-1611312449408-fcece27cdbb7?q=80&w=669&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "clothing"},
    {"id": 11, "name": "Woven, Self Design Banarasi Silk Blend, Pure Silk Saree", "price": 2000.99, "imageUrl": "https://images.unsplash.com/photo-1727430228383-aa1fb59db8bf?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "clothing", "salePrice": 5000.99},

    {"id": 12, "name": "Sneakers For Men ", "price": 2000.99, "imageUrl": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "shoes"},
    {"id": 13, "name": "Women Flats Sandal ", "price": 500, "imageUrl": "https://plus.unsplash.com/premium_photo-1676234844384-82e1830af724?q=80&w=688&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "shoes", "salePrice": 1500.99},
    {"id": 14, "name": "white sneaker", "price": 2000.99, "imageUrl": "https://images.unsplash.com/photo-1512374382149-233c42b6a83b?q=80&w=735&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "shoes"},
    {"id": 15, "name": "Flip Flop", "price": 200, "imageUrl": "https://images.unsplash.com/photo-1568901578471-a1d5af772617?q=80&w=745&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "category": "shoes", "salePrice": 1200},


]


def home(request):
    """Render the main shop page."""
    return render(request, "index.html")


def products(request):
    """Return the list of products as JSON."""
    return JsonResponse(PRODUCTS, safe=False)


@csrf_exempt
def checkout(request):
    """Accept a cart JSON payload, log it, and return success."""
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        cart = payload.get("cart", [])
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # Log order to console (server log)
    print("Received order:", cart)

    return JsonResponse({"message": "Order received! Thank you for your purchase."})
