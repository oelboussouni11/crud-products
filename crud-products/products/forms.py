# products/forms.py
from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "stock",
                  "description", "image", "image_url"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Atlas Tee"}),
            "category": forms.TextInput(attrs={"placeholder": "T-Shirts"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "25.00"}),
            "stock": forms.NumberInput(attrs={"min": "0", "placeholder": "0"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Details…"}),
            "image": forms.FileInput(attrs={"accept": "image/*", "id": "id_image", "style": "display:none"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://example.com/image.jpg"}),
        }


class CSVUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV file",
        widget=forms.FileInput(
            attrs={"accept": ".csv", "id": "id_csv", "style": "display:none"})
    )
    strict = forms.BooleanField(
        required=False,
        initial=False,
        label="Strict mode (abort if any row has errors)"
    )
