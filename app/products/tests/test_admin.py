import json
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, SimpleTestCase

from products.admin import ProductAdmin
from products.integrations.together import TogetherAPIError
from products.models import Product


class ProductAdminDescriptionTests(SimpleTestCase):
    def setUp(self):
        self.model_admin = ProductAdmin(Product, admin.site)
        self.factory = RequestFactory()

    @patch("products.admin.generate_product_description", side_effect=TogetherAPIError("Сервис недоступен"))
    def test_returns_provider_error_without_server_traceback(self, _generate_description):
        request = self.factory.post(
            "/admin/products/product/generate-description/",
            data=json.dumps({"name": "Пиво"}),
            content_type="application/json",
        )

        response = self.model_admin.generate_description_view(request)

        self.assertEqual(response.status_code, 502)
        self.assertJSONEqual(response.content, {"error": "Сервис недоступен"})
