import json
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from label_printer.views import print_label


class PrintLabelViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("label_printer.views.print_product_label")
    def test_passes_only_product_identifier_and_volume_to_service(self, print_product_label):
        request = self.factory.post(
            "/labels/print/",
            data=json.dumps({"product_id": 17, "volume": 1500}),
            content_type="application/json",
        )

        response = print_label(request)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})
        print_product_label.assert_called_once_with(product_id=17, volume=1500)

    def test_rejects_invalid_json(self):
        request = self.factory.post("/labels/print/", data="not-json", content_type="application/json")

        response = print_label(request)

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"success": False, "error": "Неверный формат данных"})
