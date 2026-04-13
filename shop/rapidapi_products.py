"""
RapidAPI Amazon/Flipkart Product Fetcher
Easier alternative to official Amazon API
Requires: RapidAPI account and subscription

Popular APIs on RapidAPI:
- Real-Time Amazon Data (by Zyla Labs)
- Amazon Price & Product Data
- Flipkart Product Data (unofficial)
"""
import requests
import json
from django.conf import settings

class RapidAPIProductFetcher:
    """
    Fetch products from Amazon/Flipkart via RapidAPI
    More reliable than scraping, legal gray area but commonly used
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'RAPIDAPI_KEY', None)
        self.base_headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': ''  # Set per endpoint
        }
    
    def fetch_amazon_search(self, query, page=1):
        """
        Search Amazon products using Real-Time Amazon Data API
        
        API: https://rapidapi.com/zyla-labs-zyla-labs-default/api/real-time-amazon-data
        Pricing: Free tier: 100 requests/month
        """
        if not self.api_key:
            print("RapidAPI key not configured")
            return []
        
        url = "https://real-time-amazon-data.p.rapidapi.com/search"
        
        querystring = {
            "query": query,
            "page": str(page),
            "country": "IN",  # India
            "sort_by": "RELEVANCE",
            "product_condition": "ALL"
        }
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }
        
        try:
            print(f"[RapidAPI] Making request to: {url}")
            print(f"[RapidAPI] Query: {query}")
            print(f"[RapidAPI] Headers: {headers}")
            print(f"[RapidAPI] Params: {querystring}")
            
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            
            print(f"[RapidAPI] Status Code: {response.status_code}")
            print(f"[RapidAPI] Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[RapidAPI] Response Data: {data}")
                return self.format_amazon_products(data)
            else:
                print(f"[RapidAPI] API Error: {response.status_code}")
                print(f"[RapidAPI] Error Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"[RapidAPI] Error fetching from RapidAPI: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_amazon_deals(self):
        """
        Fetch Amazon deals and bestsellers
        
        API: https://rapidapi.com/zyla-labs-zyla-labs-default/api/real-time-amazon-data
        Endpoint: /deals
        """
        if not self.api_key:
            return []
        
        url = "https://real-time-amazon-data.p.rapidapi.com/deals-v2"
        
        querystring = {
            "country": "IN",
            "page": "1",
            "sort_by": "FEATURED"
        }
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            if response.status_code == 200:
                return self.format_amazon_products(response.json())
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def format_amazon_products(self, data):
        """Convert Amazon API response to our product format"""
        products = []
        
        print(f"[RapidAPI] Formatting products from data: {data}")
        
        items = data.get('data', {}).get('products', [])
        print(f"[RapidAPI] Found {len(items)} items in response")
        
        if not items:
            # Try alternative response structure
            items = data.get('products', [])
            print(f"[RapidAPI] Trying alternative structure, found {len(items)} items")
        
        for idx, item in enumerate(items, 1):
            try:
                print(f"[RapidAPI] Processing item {idx}: {item}")
                
                # Extract price - handle different formats
                price_info = item.get('product_price', '0')
                price_num = self.extract_price(price_info)
                
                # Original price (if on sale)
                original_price = item.get('product_original_price', price_info)
                original_num = self.extract_price(original_price)
                
                product = {
                    'id': 1000 + idx,  # Offset to avoid conflicts
                    'name': item.get('product_title', 'Unknown'),
                    'price': original_num if original_num > price_num else price_num,
                    'salePrice': price_num if price_num < original_num else None,
                    'imageUrl': item.get('product_photo', ''),
                    'category': item.get('product_category', 'Amazon'),
                    'description': f"Rating: {item.get('product_star_rating', 'N/A')}",
                    'external_url': item.get('product_url', ''),
                    'asin': item.get('asin', ''),
                    'source': 'amazon'
                }
                products.append(product)
                print(f"[RapidAPI] Successfully formatted product: {product['name']}")
            except Exception as e:
                print(f"Error formatting product: {e}")
                continue
        
        print(f"[RapidAPI] Returning {len(products)} formatted products")
        return products
    
    def extract_price(self, price_str):
        """Extract numeric price from string like '₹1,999.00'"""
        if not price_str:
            return 0
        
        # Remove currency symbols and commas
        import re
        numeric = re.sub(r'[^\d.]', '', str(price_str))
        try:
            return float(numeric) if numeric else 0
        except:
            return 0
    
    def fetch_multiple_categories(self, categories, items_per_category=20):
        """
        Fetch products from multiple Amazon categories
        
        Args:
            categories: List of category names to search
            items_per_category: Items to fetch per category
        
        Returns:
            List of products from all categories
        """
        all_products = []
        
        for category in categories:
            print(f"Fetching {items_per_category} products for: {category}")
            
            # Calculate pages needed (API returns ~10 per page)
            pages_needed = (items_per_category + 9) // 10
            
            for page in range(1, pages_needed + 1):
                products = self.fetch_amazon_search(category, page=page)
                all_products.extend(products)
                
                # Stop if we have enough
                if len(all_products) >= len(categories) * items_per_category:
                    break
        
        return all_products[:len(categories) * items_per_category]


# Django Integration
from .models import Product

def import_amazon_products_to_db(categories=None, items_per_category=50):
    """
    Import Amazon products into the database
    
    Usage:
        from shop.rapidapi_products import import_amazon_products_to_db
        import_amazon_products_to_db(
            categories=['Electronics', 'Fashion', 'Home'],
            items_per_category=50
        )
    """
    fetcher = RapidAPIProductFetcher()
    
    categories = categories or [
        'Electronics', 'Fashion', 'Home', 'Books', 
        'Beauty', 'Sports', 'Toys', 'Grocery'
    ]
    
    # Fetch products
    products = fetcher.fetch_multiple_categories(categories, items_per_category)
    
    print(f"Fetched {len(products)} products from Amazon")
    
    # Clear existing mock data (optional)
    # Product.objects.filter(source='amazon').delete()
    
    # Save to database
    created_count = 0
    for product_data in products:
        try:
            # Check if product already exists (by ASIN)
            existing = Product.objects.filter(
                external_id=product_data.get('asin'),
                source='amazon'
            ).first()
            
            if existing:
                continue
            
            # Create new product
            Product.objects.create(
                name=product_data['name'][:200],  # Truncate if too long
                price=product_data['price'],
                sale_price=product_data.get('salePrice'),
                image_url=product_data['imageUrl'],
                category=product_data['category'],
                description=product_data.get('description', ''),
                external_id=product_data.get('asin'),
                external_url=product_data.get('external_url'),
                source='amazon'
            )
            created_count += 1
            
        except Exception as e:
            print(f"Error saving product: {e}")
            continue
    
    print(f"Successfully imported {created_count} new products")
    return created_count


# Affiliate Link Generator
def get_amazon_affiliate_link(base_url, associate_tag):
    """
    Convert Amazon product URL to affiliate link
    
    Args:
        base_url: Original Amazon product URL
        associate_tag: Your Amazon Associates ID
    """
    import urllib.parse
    
    # Parse URL
    parsed = urllib.parse.urlparse(base_url)
    
    # Add associate tag to query params
    query_params = urllib.parse.parse_qs(parsed.query)
    query_params['tag'] = [associate_tag]
    
    # Rebuild URL
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    affiliate_url = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    
    return affiliate_url


# Wrapper functions for views.py compatibility
def fetch_amazon_products(category, count=50):
    """
    Fetch Amazon products for a single category.
    Wrapper for views.py to use.
    
    Args:
        category: Category name to search
        count: Number of products to fetch
    
    Returns:
        List of product dictionaries
    """
    fetcher = RapidAPIProductFetcher()
    
    # Calculate pages needed (API returns ~10 per page)
    pages_needed = (count + 9) // 10
    all_products = []
    
    for page in range(1, pages_needed + 1):
        products = fetcher.fetch_amazon_search(category, page=page)
        all_products.extend(products)
        
        if len(all_products) >= count:
            break
    
    # Add category to each product
    for product in all_products:
        product['category'] = category
    
    return all_products[:count]


def import_products_to_db(products_data, default_category='General'):
    """
    Import products to database.
    Wrapper for views.py to use.
    
    Args:
        products_data: List of product dictionaries
        default_category: Default category if not in product data
    
    Returns:
        Number of products imported
    """
    from .models import Product
    
    created_count = 0
    for product_data in products_data:
        try:
            # Check if product already exists (by ASIN)
            existing = Product.objects.filter(
                external_id=product_data.get('asin'),
                source='amazon'
            ).first()
            
            if existing:
                continue
            
            # Get category from product data or use default
            category = product_data.get('category', default_category)
            
            # Create new product
            Product.objects.create(
                name=product_data['name'][:200],
                price=product_data['price'],
                sale_price=product_data.get('salePrice'),
                image_url=product_data.get('imageUrl', ''),
                category=category,
                description=product_data.get('description', '')[:500],
                external_id=product_data.get('asin', ''),
                external_url=product_data.get('external_url', ''),
                source='amazon',
                rating=product_data.get('rating'),
                in_stock=True
            )
            created_count += 1
            
        except Exception as e:
            print(f"Error saving product: {e}")
            continue
    
    print(f"Successfully imported {created_count} new products")
    return created_count
