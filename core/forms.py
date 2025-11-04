from django import forms
from .models import ProductDetails, Color

class ProductDetailsForm(forms.ModelForm):
    class Meta:
        model = ProductDetails
        fields = ['product', 'specifications', 'description', 'warranty', 'stock', 'image', 'colors']
        widgets = {
            'colors': forms.CheckboxSelectMultiple(),  # ye checkbox ke liye hai
        }

    # optional: checkbox ko nice layout me show karne ke liye
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['colors'].queryset = Color.objects.all().order_by('name')
        self.fields['colors'].help_text = "Select one or more colors for this product."
