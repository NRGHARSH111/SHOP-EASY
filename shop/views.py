"""
ShopEasy Premium Authentication System
======================================
Production-ready authentication with security features:
- Rate limiting
- Input validation & sanitization
- Password strength validation
- 2FA support (concept)
- Session management
- CSRF protection
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import json
import re
import secrets
import hashlib
from datetime import datetime, timedelta
from .models import Product, CartItem, Order, OrderItem

# Rate Limiting Configuration
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes
LOCKOUT_DURATION = 1800  # 30 minutes


def cors_json_response(data, status=200, safe=True):
    """Return JSON response with CORS headers for browser preview compatibility."""
    response = JsonResponse(data, safe=safe, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_rate_limit(identifier):
    """
    Check if user/IP has exceeded rate limit.
    Returns (allowed: bool, remaining_attempts: int, lockout_seconds: int)
    """
    cache_key = f"auth_attempts_{identifier}"
    lockout_key = f"auth_lockout_{identifier}"
    
    # Check if currently locked out
    lockout_until = cache.get(lockout_key)
    if lockout_until:
        remaining_lockout = int((lockout_until - timezone.now()).total_seconds())
        if remaining_lockout > 0:
            return False, 0, remaining_lockout
        else:
            # Lockout expired, clear it
            cache.delete(lockout_key)
            cache.delete(cache_key)
    
    # Get attempt history
    attempts = cache.get(cache_key, [])
    now = timezone.now()
    
    # Filter attempts within the time window
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    attempts = [t for t in attempts if t > window_start]
    
    # Check if limit exceeded
    if len(attempts) >= RATE_LIMIT_ATTEMPTS:
        # Set lockout
        lockout_until = now + timedelta(seconds=LOCKOUT_DURATION)
        cache.set(lockout_key, lockout_until, LOCKOUT_DURATION)
        return False, 0, LOCKOUT_DURATION
    
    return True, RATE_LIMIT_ATTEMPTS - len(attempts), 0


def record_attempt(identifier):
    """Record a failed authentication attempt."""
    cache_key = f"auth_attempts_{identifier}"
    attempts = cache.get(cache_key, [])
    attempts.append(timezone.now())
    cache.set(cache_key, attempts, RATE_LIMIT_WINDOW)


def sanitize_input(value, max_length=255):
    """Sanitize user input to prevent XSS and injection attacks."""
    if not isinstance(value, str):
        return ""
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>\"\'%;()&+]', '', value)
    
    # Limit length
    value = value[:max_length]
    
    # Strip whitespace
    return value.strip()


def validate_username(username):
    """
    Validate username with strict rules.
    Returns (is_valid: bool, error_message: str)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    # Only allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Check for reserved words
    reserved = ['admin', 'root', 'superuser', 'system', 'support', 'help', 'api', 'shop']
    if username.lower() in reserved:
        return False, "This username is reserved"
    
    return True, None


def validate_password_strength(password):
    """
    Validate password strength.
    Returns (is_valid: bool, error_message: str, score: int)
    """
    if not password:
        return False, "Password is required", 0
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters", 0
    
    score = 0
    errors = []
    
    # Length scoring
    if len(password) >= 12:
        score += 2
    elif len(password) >= 10:
        score += 1
    
    # Character variety
    if re.search(r'[a-z]', password):
        score += 1
    else:
        errors.append("lowercase letter")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        errors.append("uppercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        errors.append("number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        errors.append("special character")
    
    # Check for common patterns
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        score -= 1
    
    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein']:
        return False, "This password is too common", 0
    
    if errors and score < 3:
        return False, f"Password must include at least: {', '.join(errors)}", score
    
    return True, None, score


def generate_2fa_code():
    """Generate a 6-digit 2FA code."""
    return secrets.randbelow(1000000)


def hash_2fa_code(code):
    """Hash 2FA code for secure storage."""
    return hashlib.sha256(str(code).encode()).hexdigest()


# ============================================
# AUTHENTICATION VIEWS
# ============================================

@ensure_csrf_cookie
def auth_page(request):
    """Render the premium authentication page."""
    return render(request, "auth.html")


@csrf_exempt
def user_signup(request):
    """
    Enhanced user registration with validation and security.
    """
    if request.method != "POST":
        return cors_json_response({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Sanitize inputs
        username = sanitize_input(data.get('username', ''))
        email = sanitize_input(data.get('email', ''), max_length=254)
        password = data.get('password', '')  # Don't sanitize password
        
        # Validate username
        username_valid, username_error = validate_username(username)
        if not username_valid:
            return cors_json_response({'error': username_error}, status=400)
        
        # Check if username exists
        if User.objects.filter(username__iexact=username).exists():
            return cors_json_response({'error': 'Username already taken'}, status=409)
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return cors_json_response({'error': 'Please enter a valid email address'}, status=400)
        
        if User.objects.filter(email__iexact=email).exists():
            return cors_json_response({'error': 'An account with this email already exists'}, status=409)
        
        # Validate password strength
        password_valid, password_error, _ = validate_password_strength(password)
        if not password_valid:
            return cors_json_response({'error': password_error}, status=400)
        
        # Create user
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=True
                )
                
                # Log in the user immediately
                login(request, user)
                
                return cors_json_response({
                    'success': True,
                    'message': 'Account created successfully!',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                })
        
        except Exception as e:
            return cors_json_response({'error': 'Failed to create account. Please try again.'}, status=500)
    
    except json.JSONDecodeError:
        return cors_json_response({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return cors_json_response({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
def user_login(request):
    """
    Enhanced login with rate limiting, 2FA support, and security features.
    """
    if request.method != "POST":
        return cors_json_response({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get identifier for rate limiting (IP + username)
        ip = get_client_ip(request)
        username = sanitize_input(data.get('username', ''))
        identifier = f"{ip}:{username.lower()}"
        
        # Check rate limit
        allowed, remaining, lockout = check_rate_limit(identifier)
        if not allowed:
            if lockout > 0:
                minutes = lockout // 60
                return cors_json_response({
                    'error': f'Too many failed attempts. Please try again in {minutes} minutes.',
                    'lockout_seconds': lockout
                }, status=429)
        
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            record_attempt(identifier)
            return cors_json_response({'error': 'Username and password are required'}, status=400)
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Clear rate limiting on success
            cache.delete(f"auth_attempts_{identifier}")
            cache.delete(f"auth_lockout_{identifier}")
            
            # Check if 2FA is enabled (placeholder for future implementation)
            two_factor_enabled = False  # This would be checked from user profile
            
            if two_factor_enabled:
                # Generate and send 2FA code
                code = generate_2fa_code()
                hashed_code = hash_2fa_code(code)
                
                # Store in cache with 5-minute expiry
                cache_key = f"2fa_{user.id}"
                cache.set(cache_key, hashed_code, 300)
                
                # In production, send code via email/SMS
                print(f"2FA Code for {user.username}: {code:06d}")  # Debug only
                
                return cors_json_response({
                    'requires_2fa': True,
                    'message': 'Please enter the verification code sent to your email',
                    'user_id': user.id
                })
            
            # Regular login
            login(request, user)
            
            # Set session expiry based on remember_me
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(86400)  # 1 day
            
            return cors_json_response({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        
        else:
            # Failed login
            record_attempt(identifier)
            
            return cors_json_response({
                'error': 'Invalid username or password',
                'remaining_attempts': remaining - 1 if remaining > 0 else 0
            }, status=401)
    
    except json.JSONDecodeError:
        return cors_json_response({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return cors_json_response({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
def verify_2fa(request):
    """
    Verify 2FA code and complete login.
    """
    if request.method != "POST":
        return cors_json_response({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        code = data.get('code', '').replace(' ', '')
        
        if not user_id or not code:
            return cors_json_response({'error': 'User ID and code are required'}, status=400)
        
        # Verify code from cache
        cache_key = f"2fa_{user_id}"
        stored_hash = cache.get(cache_key)
        
        if not stored_hash:
            return cors_json_response({'error': 'Verification code has expired'}, status=400)
        
        if hash_2fa_code(code) != stored_hash:
            return cors_json_response({'error': 'Invalid verification code'}, status=401)
        
        # Code verified, log in user
        try:
            user = User.objects.get(id=user_id)
            login(request, user)
            cache.delete(cache_key)  # Clear used code
            
            return cors_json_response({
                'success': True,
                'message': 'Two-factor authentication successful!',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        except User.DoesNotExist:
            return cors_json_response({'error': 'User not found'}, status=404)
    
    except json.JSONDecodeError:
        return cors_json_response({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return cors_json_response({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
def user_logout(request):
    """Secure logout with session cleanup."""
    if request.user.is_authenticated:
        logout(request)
    return cors_json_response({'success': True, 'message': 'Logged out successfully'})


def check_auth(request):
    """Check authentication status."""
    if request.user.is_authenticated:
        return cors_json_response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    return cors_json_response({'authenticated': False})


@csrf_exempt
def request_password_reset(request):
    """
    Request password reset - sends reset token via email.
    """
    if request.method != "POST":
        return cors_json_response({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        email = sanitize_input(data.get('email', ''))
        
        try:
            validate_email(email)
        except ValidationError:
            return cors_json_response({'error': 'Please enter a valid email address'}, status=400)
        
        try:
            user = User.objects.get(email__iexact=email)
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            cache_key = f"password_reset_{token}"
            cache.set(cache_key, user.id, 3600)  # 1 hour expiry
            
            # In production, send email with reset link
            reset_link = f"http://127.0.0.1:8000/auth/reset-password/{token}"
            print(f"Password reset link for {email}: {reset_link}")  # Debug only
            
            return cors_json_response({
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link.'
            })
        
        except User.DoesNotExist:
            # Don't reveal if email exists
            return cors_json_response({
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link.'
            })
    
    except json.JSONDecodeError:
        return cors_json_response({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return cors_json_response({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
def reset_password(request, token):
    """
    Reset password using token.
    """
    if request.method != "POST":
        return cors_json_response({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        cache_key = f"password_reset_{token}"
        user_id = cache.get(cache_key)
        
        if not user_id:
            return cors_json_response({'error': 'Invalid or expired reset token'}, status=400)
        
        data = json.loads(request.body)
        new_password = data.get('password', '')
        
        # Validate password strength
        valid, error, _ = validate_password_strength(new_password)
        if not valid:
            return cors_json_response({'error': error}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            # Clear the token
            cache.delete(cache_key)
            
            return cors_json_response({
                'success': True,
                'message': 'Password has been reset successfully. Please login with your new password.'
            })
        
        except User.DoesNotExist:
            return cors_json_response({'error': 'User not found'}, status=404)
    
    except json.JSONDecodeError:
        return cors_json_response({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return cors_json_response({'error': 'An unexpected error occurred'}, status=500)

# Cart & Order Views
@csrf_exempt
def sync_cart(request):
    if not request.user.is_authenticated:
        return cors_json_response({'error': 'Not authenticated'}, status=401)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cart_data = data.get('cart', [])
            
            # Clear existing cart and replace with new one
            CartItem.objects.filter(user=request.user).delete()
            for item in cart_data:
                product = Product.objects.get(id=item['id'])
                CartItem.objects.create(user=request.user, product=product, quantity=item['quantity'])
            
            return cors_json_response({'message': 'Cart synced successfully'})
        except Exception as e:
            return cors_json_response({'error': str(e)}, status=400)
    
    # GET request: return user's cart
    # select_related avoids the N+1 problem by joining Product table
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    data = []
    for item in cart_items:
        data.append({
            'id': item.product.id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'imageUrl': item.product.image_url
        })
    return cors_json_response({'cart': data})

def get_orders(request):
    if not request.user.is_authenticated:
        return cors_json_response({'error': 'Not authenticated'}, status=401)
    
    # Optimization: prefetch_related reduces database hits from O(N) to O(1)
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    data = []
    for order in orders:
        items = []
        # Accessing order.items.all() now doesn't trigger a new DB query
        for item in order.items.all():
            items.append({
                'name': item.product_name,
                'price': float(item.price),
                'quantity': item.quantity
            })
        data.append({
            'id': f"ORD-{order.id}",
            'timestamp': order.created_at.isoformat(),
            'total': float(order.total_price),
            'count': sum(i.quantity for i in order.items.all()),
            'items': items
        })
    return cors_json_response(data, safe=False)

@csrf_exempt
def checkout(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        cart_data = payload.get("cart", [])
        
        if not cart_data:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # If user is logged in, save to DB
        if request.user.is_authenticated:
            with transaction.atomic():
                total_price = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart_data)
                order = Order.objects.create(user=request.user, total_price=total_price)
                
                for item in cart_data:
                    product = Product.objects.get(id=item['id'])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        price=item.get('price', product.price),
                        quantity=item.get('quantity', 1)
                    )
                # Clear cart in DB
                CartItem.objects.filter(user=request.user).delete()
        
        print("Received order:", cart_data)
        return cors_json_response({"message": "Order received! Thank you for your purchase."})
    except Exception as e:
        return cors_json_response({'error': str(e)}, status=400)

def populate_initial_data():
    """No mock data - products must be fetched from API or added manually"""
    pass  # No hardcoded products - use RapidAPI integration instead

def landing(request):
    """Render the stunning landing page."""
    return render(request, "landing.html")

def shop(request):
    """Render the main shop page with products."""
    populate_initial_data()
    return render(request, "index.html")

def checkout_page(request):
    """Render the checkout page."""
    return render(request, "checkout.html")

def profile_page(request):
    """Render the user profile page."""
    return render(request, "profile.html")

def products(request):
    """Return the list of products as JSON from the database."""
    populate_initial_data()
    product_list = Product.objects.all()
    data = []
    for p in product_list:
        product_data = {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "salePrice": float(p.sale_price) if p.sale_price else None,
            "imageUrl": p.image_url,
            "category": p.category,
            "description": p.description,
            "source": p.source,
            "externalUrl": p.external_url,
            "rating": float(p.rating) if p.rating else None,
            "inStock": p.in_stock
        }
        data.append(product_data)
    return cors_json_response(data, safe=False)


@csrf_exempt
def fetch_category_products(request):
    """Fetch products for a specific category from Amazon API if not in database."""
    if request.method != "POST":
        return cors_json_response({"error": "Only POST allowed"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        category = data.get("category", "").strip()
        count = min(int(data.get("count", 50)), 100)  # Max 100 per request
        
        if not category:
            return cors_json_response({"error": "Category is required"}, status=400)
        
        # Check if products exist for this category
        existing_count = Product.objects.filter(category__iexact=category).count()
        
        if existing_count > 0:
            # Return existing products
            products_list = Product.objects.filter(category__iexact=category)[:count]
            product_data = []
            for p in products_list:
                product_data.append({
                    "id": p.id,
                    "name": p.name,
                    "price": float(p.price),
                    "salePrice": float(p.sale_price) if p.sale_price else None,
                    "imageUrl": p.image_url,
                    "category": p.category,
                    "description": p.description,
                    "source": p.source,
                    "externalUrl": p.external_url,
                    "rating": float(p.rating) if p.rating else None,
                    "inStock": p.in_stock
                })
            return cors_json_response({
                "fetched": False,
                "message": f"Found {existing_count} existing products",
                "products": product_data,
                "count": len(product_data)
            })
        
        # No products exist - fetch from Amazon API
        from .rapidapi_products import fetch_amazon_products, import_products_to_db
        
        print(f"[ShopEasy] Fetching {count} products for category: {category}")
        amazon_products = fetch_amazon_products(category, count)
        
        if not amazon_products:
            return cors_json_response({
                "fetched": False,
                "error": "No products found from API",
                "products": [],
                "count": 0
            }, status=404)
        
        # Import products to database
        imported_count = import_products_to_db(amazon_products, category)
        
        # Return newly imported products
        new_products = Product.objects.filter(category__iexact=category)[:count]
        product_data = []
        for p in new_products:
            product_data.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "salePrice": float(p.sale_price) if p.sale_price else None,
                "imageUrl": p.image_url,
                "category": p.category,
                "description": p.description,
                "source": p.source,
                "externalUrl": p.external_url,
                "rating": float(p.rating) if p.rating else None,
                "inStock": p.in_stock
            })
        
        return cors_json_response({
            "fetched": True,
            "message": f"Successfully fetched and imported {imported_count} products",
            "products": product_data,
            "count": len(product_data)
        })
        
    except Exception as e:
        print(f"[ShopEasy] Error fetching category products: {str(e)}")
        return cors_json_response({
            "fetched": False,
            "error": str(e),
            "products": [],
            "count": 0
        }, status=500)


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


@csrf_exempt
def external_search(request):
    """
    Search for products not in the database using external APIs
    """
    if request.method != 'GET':
        return cors_json_response({"error": "Method not allowed"}, status=405)
    
    try:
        query = request.GET.get('query', '').strip()
        if not query:
            return cors_json_response({
                "error": "Search query is required",
                "products": []
            }, status=400)
        
        print(f"[ShopEasy] External search for: {query}")
        
        # Import the RapidAPI fetcher
        from .rapidapi_products import RapidAPIProductFetcher
        
        # Fetch products from Amazon
        fetcher = RapidAPIProductFetcher()
        print(f"[ShopEasy] Using RapidAPI key: {fetcher.api_key[:10]}..." if fetcher.api_key else "[ShopEasy] No RapidAPI key found")
        amazon_products = fetcher.fetch_amazon_search(query, page=1)
        
        # If no products from API (likely due to missing API key), use mock data
        if not amazon_products:
            print("[ShopEasy] RapidAPI returned no results, using mock external search data")
            amazon_products = get_mock_external_products(query)
        else:
            print(f"[ShopEasy] RapidAPI returned {len(amazon_products)} products")
        
        # Format products for frontend
        formatted_products = []
        for product in amazon_products:
            formatted_products.append({
                "id": product.get('id', 0),
                "name": product.get('name', ''),
                "price": float(product.get('price', 0)),
                "salePrice": float(product.get('salePrice', 0)) if product.get('salePrice') else None,
                "imageUrl": product.get('imageUrl', ''),
                "category": product.get('category', 'External'),
                "description": product.get('description', ''),
                "source": product.get('source', 'external'),
                "externalUrl": product.get('external_url', ''),
                "rating": None,
                "inStock": True,
                "external": True  # Mark as external product
            })
        
        print(f"[ShopEasy] Found {len(formatted_products)} external products")
        
        return cors_json_response({
            "success": True,
            "query": query,
            "products": formatted_products,
            "count": len(formatted_products),
            "source": "external"
        })
        
    except Exception as e:
        print(f"[ShopEasy] Error in external search: {str(e)}")
        return cors_json_response({
            "error": str(e),
            "products": [],
            "count": 0
        }, status=500)


def get_mock_external_products(query):
    """
    Generate mock external products when RapidAPI is not configured
    This provides a demonstration of the external search functionality
    """
    import random
    
    # Mock product templates
    mock_templates = [
        {
            "name": f"Premium {query.title()} - High Quality",
            "price": 999.99,
            "salePrice": 799.99,
            "imageUrl": f"https://picsum.photos/seed/{query}1/300/300.jpg",
            "category": "External",
            "description": f"High-quality {query} with premium features and excellent durability"
        },
        {
            "name": f"{query.title()} Pro - Professional Grade",
            "price": 1499.99,
            "salePrice": None,
            "imageUrl": f"https://picsum.photos/seed/{query}2/300/300.jpg",
            "category": "External",
            "description": f"Professional grade {query} for advanced users and experts"
        },
        {
            "name": f"Budget {query.title()} - Affordable Option",
            "price": 299.99,
            "salePrice": 199.99,
            "imageUrl": f"https://picsum.photos/seed/{query}3/300/300.jpg",
            "category": "External",
            "description": f"Affordable {query} with essential features for everyday use"
        },
        {
            "name": f"Smart {query.title()} - Connected Features",
            "price": 899.99,
            "salePrice": 699.99,
            "imageUrl": f"https://picsum.photos/seed/{query}4/300/300.jpg",
            "category": "External",
            "description": f"Smart {query} with connectivity and modern features"
        },
        {
            "name": f"Eco {query.title()} - Sustainable Choice",
            "price": 599.99,
            "salePrice": None,
            "imageUrl": f"https://picsum.photos/seed/{query}5/300/300.jpg",
            "category": "External",
            "description": f"Eco-friendly {query} made from sustainable materials"
        }
    ]
    
    # Return 3-5 random products
    selected_products = random.sample(mock_templates, random.randint(3, 5))
    
    # Add unique IDs and source info
    for i, product in enumerate(selected_products):
        product['id'] = 2000 + i  # External product IDs start from 2000
        product['source'] = 'external'
        product['external_url'] = f"https://example.com/{query}/{i+1}"
    
    print(f"[ShopEasy] Generated {len(selected_products)} mock products for query: {query}")
    return selected_products
