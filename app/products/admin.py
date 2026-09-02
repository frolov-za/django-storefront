from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from .models import Product, Tare
from products.integrations.together import TogetherAPIError
from products.services.descriptions import generate_product_description
import json

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fields = ('name', 'barcode', 'barcode15', 'image', 'description', 'generate_button')
    list_display = ('id', 'name', 'barcode', 'barcode15')
    search_fields = ('name', 'barcode', 'barcode15')
    readonly_fields = ('generate_button',)

    def generate_button(self, obj=None):
        return mark_safe("""
        <button type="button" id="generate-description" class="button">Сгенерировать описание</button>
        <script>
        document.addEventListener("DOMContentLoaded", function() {
            const button = document.getElementById("generate-description");
            if (button) {
                button.addEventListener("click", async function() {
                    const name = document.getElementById("id_name").value;
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                    const response = await fetch("/admin/products/product/generate-description/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken
                        },
                        body: JSON.stringify({ name })
                    });

                    const data = await response.json();
                    if (data.description) {
                        document.getElementById("id_description").value = data.description;
                    } else {
                        alert("Ошибка генерации: " + (data.error || "неизвестная ошибка"));
                    }
                });
            }
        });
        </script>
        """)

@admin.register(Tare)
class TareAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "type")
    list_filter = ("type",)
    search_fields = ("name",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("generate-description/", self.admin_site.admin_view(self.generate_description_view), name="generate_description"),
        ]
        return custom_urls + urls

    def generate_description_view(self, request):
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                name = data.get("name", "").strip()
                if not name:
                    return JsonResponse({"error": "Название не указано"}, status=400)
                description = generate_product_description(name)
                return JsonResponse({"description": description})
            except TogetherAPIError as error:
                return JsonResponse({"error": str(error)}, status=502)
            except Exception:
                return JsonResponse({"error": "Не удалось сгенерировать описание"}, status=500)
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)
