from django.test import TestCase, Client

# Create your tests here.

class ProductsApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_products_endpoint_returns_200_and_list(self):
        resp = self.client.get("/api/products/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 5)

    def test_product_item_has_expected_fields(self):
        resp = self.client.get("/api/products/")
        data = resp.json()
        item = data[0]
        self.assertIn("id", item)
        self.assertIn("name", item)
        self.assertIn("price", item)
        self.assertIn("imageUrl", item)
