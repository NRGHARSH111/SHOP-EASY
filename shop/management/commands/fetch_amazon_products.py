"""
Django Management Command: Fetch Amazon Products
Usage: python manage.py fetch_amazon_products --categories Electronics Fashion --count 100
"""
from django.core.management.base import BaseCommand
from shop.rapidapi_products import import_amazon_products_to_db

class Command(BaseCommand):
    help = 'Fetch products from Amazon via RapidAPI and import to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            nargs='+',
            default=['Electronics', 'Fashion', 'Home', 'Books'],
            help='Product categories to fetch (default: Electronics Fashion Home Books)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of products per category (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Amazon products before importing'
        )

    def handle(self, *args, **options):
        categories = options['categories']
        count = options['count']
        clear = options['clear']
        
        self.stdout.write(self.style.NOTICE(f'Fetching {count} products per category...'))
        self.stdout.write(self.style.NOTICE(f'Categories: {", ".join(categories)}'))
        
        if clear:
            from shop.models import Product
            deleted = Product.objects.filter(source='amazon').delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted[0]} existing Amazon products'))
        
        # Import products
        imported = import_amazon_products_to_db(
            categories=categories,
            items_per_category=count
        )
        
        if imported > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported} Amazon products'))
        else:
            self.stdout.write(self.style.ERROR('No products imported. Check RapidAPI configuration.'))
