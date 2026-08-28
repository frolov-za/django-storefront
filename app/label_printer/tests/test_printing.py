from django.test import SimpleTestCase

from label_printer.services.printing import PrintingError, print_product_label


class CataloguePrintingValidationTests(SimpleTestCase):
    def test_rejects_unknown_volume_before_accessing_database(self):
        with self.assertRaisesMessage(PrintingError, "Поддерживаются только объёмы 1 и 1,5 литра"):
            print_product_label(product_id=1, volume=500)
