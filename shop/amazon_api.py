"""
Amazon Product Advertising API Integration
Requires: Amazon Associates account + API credentials
"""
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import quote, urlencode
import json

class AmazonAPI:
    """Amazon Product Advertising API 5.0 Client"""
    
    def __init__(self, access_key, secret_key, partner_tag, region='us-east-1'):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag  # Your Associates ID
        self.region = region
        self.host = f'webservices.amazon.{self.get_domain()}'
        self.endpoint = f'https://{self.host}/paapi5/searchitems'
        
    def get_domain(self):
        domains = {
            'us-east-1': 'com',
            'eu-west-1': 'co.uk',
            'ap-south-1': 'in',  # India
        }
        return domains.get(self.region, 'com')
    
    def generate_signature(self, payload, timestamp):
        """Generate AWS Signature Version 4"""
        method = 'POST'
        uri = '/paapi5/searchitems'
        service = 'ProductAdvertisingAPI'
        
        # Create canonical request
        headers = {
            'host': self.host,
            'x-amz-target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
            'content-type': 'application/json',
            'x-amz-date': timestamp
        }
        
        # Sign the request
        string_to_sign = f"{method}\n{uri}\n\n{json.dumps(payload)}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def search_items(self, keywords, search_index='All', item_count=10):
        """
        Search for products on Amazon
        
        Args:
            keywords: Search keywords
            search_index: Category (All, Electronics, Fashion, etc.)
            item_count: Number of results (max 10 per request)
        """
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        payload = {
            'Keywords': keywords,
            'SearchIndex': search_index,
            'ItemCount': item_count,
            'Resources': [
                'Images.Primary.Large',
                'ItemInfo.Title',
                'Offers.Listings.Price',
                'CustomerReviews.StarRating',
                'BrowseNodeInfo.BrowseNodes',
                'DetailPageURL'
            ],
            'PartnerTag': self.partner_tag,
            'PartnerType': 'Associates',
            'Marketplace': f'www.amazon.{self.get_domain()}'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Amz-Date': timestamp,
            'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
            'Authorization': f'AWS4-HMAC-SHA256 Credential={self.access_key}'
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.format_products(data)
            else:
                print(f"Amazon API Error: {response.status_code}")
                print(response.text)
                return []
                
        except Exception as e:
            print(f"Error fetching from Amazon: {e}")
            return []
    
    def format_products(self, data):
        """Format Amazon API response to match our product structure"""
        products = []
        
        items = data.get('SearchResult', {}).get('Items', [])
        
        for idx, item in enumerate(items, 1):
            try:
                product = {
                    'id': idx,
                    'name': item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'Unknown Product'),
                    'price': self.extract_price(item),
                    'salePrice': None,
                    'imageUrl': self.extract_image(item),
                    'category': 'Amazon',
                    'description': 'Amazon Product',
                    'amazon_url': item.get('DetailPageURL', ''),
                    'rating': item.get('CustomerReviews', {}).get('StarRating', {}).get('Value', 0)
                }
                products.append(product)
            except Exception as e:
                print(f"Error formatting product: {e}")
                continue
        
        return products
    
    def extract_price(self, item):
        """Extract price from Amazon item"""
        try:
            price_info = item.get('Offers', {}).get('Listings', [{}])[0]
            price = price_info.get('Price', {}).get('Amount', 0)
            return float(price)
        except:
            return 0
    
    def extract_image(self, item):
        """Extract image URL from Amazon item"""
        try:
            images = item.get('Images', {})
            primary = images.get('Primary', {})
            large = primary.get('Large', {})
            return large.get('URL', 'https://via.placeholder.com/300x300?text=No+Image')
        except:
            return 'https://via.placeholder.com/300x300?text=No+Image'


def get_amazon_products(categories=None, items_per_category=10):
    """
    Fetch products from Amazon for given categories
    
    Usage:
        products = get_amazon_products(
            categories=['Electronics', 'Fashion', 'Home'],
            items_per_category=10
        )
    """
    # You need to set these environment variables or configure them
    ACCESS_KEY = 'YOUR_AMAZON_ACCESS_KEY'
    SECRET_KEY = 'YOUR_AMAZON_SECRET_KEY'
    PARTNER_TAG = 'YOUR_ASSOCIATES_ID-20'
    
    if ACCESS_KEY == 'YOUR_AMAZON_ACCESS_KEY':
        print("WARNING: Amazon API credentials not configured!")
        print("Please set your Amazon PA API credentials.")
        return []
    
    api = AmazonAPI(ACCESS_KEY, SECRET_KEY, PARTNER_TAG, region='ap-south-1')
    
    all_products = []
    categories = categories or ['Electronics', 'Fashion', 'Home', 'Books']
    
    for category in categories:
        print(f"Fetching {items_per_category} products from {category}...")
        products = api.search_items(
            keywords=category,
            search_index=category,
            item_count=items_per_category
        )
        all_products.extend(products)
    
    return all_products


# Alternative: Simple affiliate link generator
def generate_amazon_affiliate_link(asin, associate_tag):
    """
    Generate affiliate link for an Amazon product
    
    Args:
        asin: Amazon product ASIN (e.g., 'B08N5WRWNW')
        associate_tag: Your Amazon Associates tag
    """
    base_url = 'https://www.amazon.in/dp'
    return f"{base_url}/{asin}?tag={associate_tag}"
