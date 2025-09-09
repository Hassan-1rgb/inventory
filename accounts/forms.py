from django import forms
from .models import AddUser
from .models import Account, AccountDetail, Category,  SubCategory, Product
from .models import Warehouse, PurchaseDetail, Purchase
from .models import StockAdjustment
from .models import Stock, Sale, SaleDetail



class SignupForm(forms.ModelForm):
    class Meta:
        model = AddUser
        fields = ['username', 'phone', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }



class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)




class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_code', 'account_name', 'is_parent']

class AccountDetailForm(forms.ModelForm):
    class Meta:
        model = AccountDetail
        fields = ['account', 'date', 'debit', 'credit', 'description']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TransactionFilterForm(forms.Form):
    account = forms.ModelChoiceField(queryset=Account.objects.all(), required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


class GeneralLedgerSummaryFrom(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))




class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['name', 'category']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'product_type', 'category', 'subcategory', 'unit', 'package', 'account']



class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location', 'description']




class PurchaseDetailForm(forms.ModelForm):
    UOM_CHOICES = (
        ('kg', 'Kilogram'),
        ('piece', 'Piece'),
    )

    uom = forms.ChoiceField(
        choices=UOM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PurchaseDetail
        fields = ['product', 'uom', 'per_unit_price', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'per_unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }



class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = '__all__'
        widgets = {
            'bill_no': forms.TextInput(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'purchase_account': forms.Select(attrs={'class': 'form-control'}),
            'new_product_entry': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),  
        }



class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ['product', 'uom', 'defective_quantity', 'description']




class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'uom', 'quantity']



class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["bill_no", "order_date", "warehouse", "sale_account", "amount"]


class SaleDetailForm(forms.ModelForm):
    class Meta:
        model = SaleDetail
        fields = ["product", "uom", "quantity", "per_unit_price", "price"]