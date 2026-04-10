# Amazon/Flipkart Product Integration Guide

## ⚠️ IMPORTANT LEGAL NOTICE

**Direct scraping of Amazon/Flipkart is:**
- ❌ Against their Terms of Service
- ❌ Illegal in most jurisdictions
- ❌ Blocked by anti-bot measures (CAPTCHA, IP blocking)
- ❌ Can result in legal action

**Legal alternatives are provided below.**

---

## ✅ OPTION 1: RapidAPI (Recommended - Easiest)

### Step 1: Sign up for RapidAPI
1. Go to https://rapidapi.com
2. Create a free account
3. Subscribe to **"Real-Time Amazon Data"** API by Zyla Labs
   - Free tier: 100 requests/month
   - Paid: $20/month for 10,000 requests

### Step 2: Get API Key
1. Go to https://rapidapi.com/zyla-labs-zyla-labs-default/api/real-time-amazon-data
2. Click "Subscribe to Test"
3. Copy your API key from the dashboard

### Step 3: Configure Django
Add to `ShopEasy/settings.py`:

```python
# RapidAPI Configuration
RAPIDAPI_KEY = 'your-rapidapi-key-here'
```

### Step 4: Run Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Fetch Amazon Products
```bash
# Fetch 50 products from 4 categories (200 total)
python manage.py fetch_amazon_products --categories Electronics Fashion Home Books --count 50

# Fetch 100 products from 10 categories (1000 total)
python manage.py fetch_amazon_products --categories Electronics Fashion Home Books Beauty Sports Toys Grocery Kitchen --count 100

# Clear existing and re-fetch
python manage.py fetch_amazon_products --categories Electronics --count 200 --clear
```

### Step 6: Update Frontend
The products will now show with "Buy on Amazon" buttons instead of "Add to Cart".

---

## ✅ OPTION 2: Amazon Product Advertising API (Official)

### Requirements
- Amazon Associates account (https://affiliate-program.amazon.in)
- Approved for Product Advertising API
- Access Key & Secret Key

### Step 1: Apply for Amazon Associates
1. Go to https://affiliate-program.amazon.in
2. Create an account
3. Wait for approval (usually 24-48 hours)
4. Get your Associate Tag (looks like: `yourname-20`)

### Step 2: Get PA API Credentials
1. Login to https://associates.amazon.in
2. Go to "Product Advertising API"
3. Generate Access Key & Secret Key

### Step 3: Configure
Edit `shop/amazon_api.py`:

```python
ACCESS_KEY = 'your-access-key'
SECRET_KEY = 'your-secret-key'
PARTNER_TAG = 'your-associate-tag-20'
```

### Limitations
- **1000 requests/day** (free tier)
- Must generate sales every 180 days to maintain access
- Rate limited
- Requires ongoing Amazon Associates compliance

---

## ✅ OPTION 3: Product Data Feeds (Affiliate Networks)

### Partner Networks
- **Cuelinks** (India focused)
- **VCommission**
- **Optimise**
- **Impact**

These provide:
- CSV/XML product feeds
- Approved product data
- Affiliate links included
- Legal compliance

---

## 🎨 Frontend Changes for External Products

### Product Card Update
Update `index.html` product card template:

```javascript
if (product.source === 'amazon' || product.source === 'flipkart') {
    // External product - redirect to affiliate link
    buttonHtml = `
        <a href="${product.external_url}" target="_blank" class="btn btn-sm add-to-cart-btn">
            <i class="fas fa-external-link-alt me-1"></i>Buy on ${product.source}
        </a>
    `;
} else {
    // Local product - add to cart
    buttonHtml = `
        <button class="btn btn-sm add-to-cart-btn" data-id="${product.id}">
            <i class="fas fa-cart-plus me-1"></i>Add
        </button>
    `;
}
```

### Badge Display
Show source badge on products:
```javascript
<span class="badge badge-float" style="background: ${product.source === 'amazon' ? '#FF9900' : '#2874F0'};">
    ${product.source}
</span>
```

---

## 📊 Expected Results

With RapidAPI (recommended):
- **1000 products** in ~10-15 minutes
- Real images, prices, ratings
- Live affiliate links
- Auto-updated on re-fetch

---

## 🔧 Troubleshooting

### "No products imported"
- Check RapidAPI key is set correctly
- Verify API subscription is active
- Check internet connection
- Look at Django console for error messages

### "API rate limit exceeded"
- RapidAPI free tier: 100 requests/month
- Wait for next month or upgrade
- Implement caching to reduce API calls

### "Products not showing"
- Run `python manage.py migrate` first
- Clear browser cache
- Check if `source='amazon'` products exist in database

---

## 💰 Monetization

### Affiliate Commissions (India)
- Electronics: 1-3%
- Fashion: 6-10%
- Home: 6-9%
- Books: 8-10%
- Beauty: 6-10%

Example: ₹10,000 TV sale = ₹100-300 commission

---

## ⚖️ Legal Compliance

### Do:
- ✅ Use official APIs
- ✅ Use affiliate networks
- ✅ Add disclosure: "As an Amazon Associate I earn from qualifying purchases"
- ✅ Display current prices (not cached)

### Don't:
- ❌ Scrape without permission
- ❌ Modify product images
- ❌ Make false claims about products
- ❌ Store outdated pricing

---

## 📞 Support

For RapidAPI issues: https://rapidapi.com/support
For Amazon API: https://affiliate-program.amazon.in/help

---

**Ready to start? Choose Option 1 (RapidAPI) for the fastest setup!** 🚀
