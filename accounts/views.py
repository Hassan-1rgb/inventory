from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.conf import settings
from twilio.rest import Client
from .models import AddUser, Account, AccountDetail, Category, SubCategory, Product, Warehouse
from .forms import SignupForm, OTPForm, LoginForm, AccountForm, AccountDetailForm, TransactionFilterForm, GeneralLedgerSummaryFrom, CategoryForm, SubCategoryForm, ProductForm, WarehouseForm
import decimal
from django.utils.dateformat import DateFormat
from datetime import datetime, date
from django.db.models import Sum
from .forms import PurchaseDetailForm, PurchaseForm
from .models import PurchaseDetail, Purchase, Vendor
import json
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from decimal import Decimal
from datetime import date, timedelta
from .models import Stock, StockAdjustment
from .forms import StockAdjustmentForm
from .forms import StockForm
from .models import Sale, SaleDetail, StockTransaction
from .forms import SaleForm, SaleDetailForm






client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# OTP Helpers
def send_otp(phone):
    try:
        verification = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )
        return verification.status == 'pending'
    except Exception as e:
        print("Twilio error:", e)
        return False

def verify_otp(phone, otp):
    try:
        verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone,
            code=otp
        )
        return verification_check.status == 'approved'
    except Exception as e:
        print("OTP verification error:", e)
        return False

# Auth Views
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_verified = False
            user.save()
            phone = f'+92{user.phone[-10:]}'  
            if send_otp(phone):
                request.session['phone'] = user.phone
                messages.success(request, "OTP sent to your phone.")
                return redirect('verify_otp')
            else:
                messages.error(request, "Failed to send OTP.")
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def verify_otp_view(request):
    phone = request.session.get('phone')
    if not phone:
        messages.error(request, "Session expired.")
        return redirect('signup')

    user = AddUser.objects.filter(phone=phone).first()
    if not user:
        messages.error(request, "User not found.")
        return redirect('signup')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            full_phone = f'+92{phone[-10:]}'
            if verify_otp(full_phone, otp):
                user.is_verified = True
                user.save()
                messages.success(request, "Phone verified successfully. Please log in.")
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP.")
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_verified:
                    auth_login(request, user)
                    return redirect('index')
                else:
                    request.session['phone'] = user.phone
                    messages.warning(request, "Phone not verified. Please verify.")
                    return redirect('verify_otp')
            else:
                messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def account_list(request):
    accounts = Account.objects.all()
    return render(request, 'accounts/account_list.html', {'accounts': accounts})

def add_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.updated_by = request.user
            account.save()
            messages.success(request, "Account added successfully.")
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'accounts/add_account.html', {'form': form})



def edit_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            account = form.save(commit=False)
            account.updated_by = request.user
            account.updated_at = now()
            account.save()
            messages.success(request, "Account updated successfully.")
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'accounts/edit_account.html', {'form': form, 'account': account})



def delete_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    if request.method == 'POST':
        account.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect('account_list')
    return render(request, 'accounts/delete_account.html', {'account': account})


def account_detail_view(request):
    if request.method == 'POST':
        form = AccountDetailForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.date:
                instance.date = date.today()
            # ✅ track created/updated by
            instance.created_by = request.user
            instance.updated_by = request.user
            instance.save()
            messages.success(request, "Entry added successfully.")
            return redirect('account_entries')
    else:
        form = AccountDetailForm(initial={'date': date.today()})
    
    details = AccountDetail.objects.all().order_by('-date')
    return render(request, 'accounts/account_detail.html', {
        'form': form,
        'details': details,
    })



def account_entries_view(request):
    entries = AccountDetail.objects.all().order_by('date') 
    return render(request, 'accounts/account_entries.html', {
        'entries': entries,
    })

def edit_entry(request, entry_id):
    entry = get_object_or_404(AccountDetail, id=entry_id)
    if request.method == 'POST':
        entry.date = request.POST.get('date')
        entry.description = request.POST.get('description')
        debit = request.POST.get('debit')
        credit = request.POST.get('credit')
        entry.debit = decimal.Decimal(debit) if debit else 0
        entry.credit = decimal.Decimal(credit) if credit else 0
        entry.save()
        messages.success(request, "Entry updated successfully.")
        return redirect('account_entries')
    return render(request, 'accounts/edit_entry.html', {'entry': entry})

def delete_entry(request, entry_id):
    entry = get_object_or_404(AccountDetail, id=entry_id)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Entry deleted successfully.")
        return redirect('account_entries')
    return render(request, 'accounts/delete_entry.html', {'entry': entry})

def transaction_view(request):
    form = TransactionFilterForm(request.GET or None)
    transactions = []
    opening_balance = 0
    closing_balance = 0
    formatted_start = formatted_end = None
    selected_account = None

    if form.is_valid():
        selected_account = form.cleaned_data['account']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        if start_date > end_date:
            messages.error(request, "Start date cannot be after end date.")
        else:
            formatted_start = DateFormat(start_date).format('F j, Y')
            formatted_end = DateFormat(end_date).format('F j, Y')

            previous_txns = AccountDetail.objects.filter(
                account=selected_account,
                date__lt=start_date
            )
            opening_balance = sum((txn.debit or 0) - (txn.credit or 0) for txn in previous_txns)

            transactions = AccountDetail.objects.filter(
                account=selected_account,
                date__range=(start_date, end_date)
            ).order_by('date')

            if not transactions:
                messages.warning(request, "No record found in the selected date range.")

            running_balance = opening_balance
            for txn in transactions:
                debit = txn.debit or 0
                credit = txn.credit or 0
                running_balance += debit - credit
                txn.running_balance = running_balance

            closing_balance = running_balance

    return render(request, 'accounts/transactions.html', {
        'form': form,
        'transactions': transactions,
        'formatted_start': formatted_start,
        'formatted_end': formatted_end,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'selected_account': selected_account,
    })

def general_ledger_summary_view(request):
    date_str = request.GET.get('date') or date.today().strftime('%Y-%m-%d')
    rows = []
    total_debit = 0
    total_credit = 0
    error = None
    warning = None
    formatted_date = ""

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        formatted_date = selected_date.strftime('%m/%d/%Y')

        transactions = AccountDetail.objects.filter(date__lte=selected_date)

        if transactions.exists():
            grouped = transactions.values(
                'account__account_code',
                'account__account_name'
            ).annotate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )

            for item in grouped:
                account_code = item['account__account_code']
                account_name = item['account__account_name']
                debit = item['total_debit'] or 0
                credit = item['total_credit'] or 0

                rows.append({
                    'account_code': account_code,
                    'account_name': account_name,
                    'debit': debit if debit > 0 else 0,
                    'credit': credit if credit > 0 else 0
                })

                total_debit += debit
                total_credit += credit
        else:
            warning = "No record found for the selected date."

    except Exception as e:
        error = f"Invalid date or error: {e}"

    context = {
        'date_input': date_str,
        'date_display': formatted_date,
        'rows': rows,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'warning': warning,
        'error': error,
        'today': date.today().strftime('%Y-%m-%d'),  
    }

    return render(request, 'accounts/general_ledger_summary.html', context)


def trial_balance_view(request): 
    start_date_str = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
    end_date_str = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')

    trial_data = []
    total_opening_debit = 0
    total_opening_credit = 0
    total_debit = 0
    total_credit = 0
    total_closing_debit = 0
    total_closing_credit = 0

    error = None
    message = None
    formatted_start_date = ""
    formatted_end_date = ""

    try:
        
        start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        formatted_start_date = start.strftime('%m/%d/%Y')
        formatted_end_date = end.strftime('%m/%d/%Y')

        accounts = Account.objects.all()

        for account in accounts:
            opening = AccountDetail.objects.filter(
                account=account,
                date__lt=start
            ).aggregate(
                debit=Sum('debit'),
                credit=Sum('credit')
            )

            opening_debit = opening['debit'] or 0
            opening_credit = opening['credit'] or 0
            net_opening = opening_debit - opening_credit

            current = AccountDetail.objects.filter(
                account=account,
                date__gte=start,
                date__lte=end
            ).aggregate(
                debit=Sum('debit'),
                credit=Sum('credit')
            )

            debit = current['debit'] or 0
            credit = current['credit'] or 0
            net_closing = net_opening + debit - credit

            if net_closing >= 0:
                closing_debit = net_closing
                closing_credit = 0
            else:
                closing_debit = 0
                closing_credit = abs(net_closing)

            if net_opening >= 0:
                opening_debit_value = net_opening
                opening_credit_value = 0
            else:
                opening_debit_value = 0
                opening_credit_value = abs(net_opening)

            trial_data.append({
                'account_code': account.account_code,
                'account_name': account.account_name,
                'opening_debit': opening_debit_value,
                'opening_credit': opening_credit_value,
                'debit': debit,
                'credit': credit,
                'closing_debit': closing_debit,
                'closing_credit': closing_credit,
            })

            total_opening_debit += opening_debit_value
            total_opening_credit += opening_credit_value
            total_debit += debit
            total_credit += credit
            total_closing_debit += closing_debit
            total_closing_credit += closing_credit

        if not trial_data:
            message = "No records found for the selected date range."

    except ValueError as e:
        error = f"Invalid date format or error: {e}"

    context = {
        'trial_data': trial_data,
        'start_date': start,
        'end_date': end,
        'date_display_start': formatted_start_date,
        'date_display_end': formatted_end_date,
        'total_opening_debit': total_opening_debit,
        'total_opening_credit': total_opening_credit,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'total_closing_debit': total_closing_debit,
        'total_closing_credit': total_closing_credit,
        'message': message,
        'error': error,
        'today': date.today().strftime('%Y-%m-%d'),
    }

    return render(request, 'accounts/trial_balance.html', context)



def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'accounts/add_category.html', {'form': form})

def manage_categories(request):
    categories = Category.objects.all()
    return render(request, 'accounts/manage_categories.html', {'categories': categories})

def product_category_list(request):
    categories = Category.objects.all()
    return render(request, 'accounts/category_list.html', {'categories': categories})



def manage_subcategories(request):
    subcategories = SubCategory.objects.select_related('category').all()
    return render(request, 'accounts/manage_subcategories.html', {'subcategories': subcategories})

def add_subcategory(request):
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_subcategories')
    else:
        form = SubCategoryForm()
    return render(request, 'accounts/add_subcategory.html', {'form': form})


def add_product_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')  # ✅ Correct URL name
    else:
        form = ProductForm()

    return render(request, 'accounts/add_product.html', {'form': form})


def product_list_view(request):
    products = Product.objects.select_related('category', 'subcategory', 'account')
    
    # Add actual stock calculation from PurchaseDetail
    for product in products:
        actual_stock = PurchaseDetail.objects.filter(
            product=product
        ).aggregate(
            total=Sum('quantity')  # updated from total_quantity → quantity
        )['total'] or 0
        
        product.actual_stock = actual_stock
    
    return render(request, 'accounts/product_list.html', {'products': products})






def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    return render(request, 'accounts/warehouse_list.html', {'warehouses': warehouses})

def add_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('warehouse_list')
    else:
        form = WarehouseForm()
    return render(request, 'accounts/warehouse_form.html', {'form': form})

def edit_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            return redirect('warehouse_list')
    else:
        form = WarehouseForm(instance=warehouse)
    return render(request, 'accounts/warehouse_form.html', {'form': form})

def delete_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        return redirect('warehouse_list')
    return render(request, 'accounts/warehouse_confirm_delete.html', {'warehouse': warehouse})




def new_product_entry(request):
    if request.method == "POST":
        form = PurchaseDetailForm(request.POST)
        purchase_id = request.POST.get("purchase_id")

        # Attach purchase if provided
        purchase = None
        if purchase_id:
            try:
                purchase = Purchase.objects.get(id=int(purchase_id))
            except (ValueError, Purchase.DoesNotExist):
                messages.warning(request, "Invalid purchase ID provided.")
                purchase = None

        if form.is_valid():
            entry = form.save(commit=False)
            entry.purchase = purchase

            # ✅ set created_by and updated_by
            if not entry.pk:  
                entry.created_by = request.user
            entry.updated_by = request.user

            entry.save()

            # ✅ Stock Update
            product = entry.product
            quantity_to_add = int(entry.quantity)

            if quantity_to_add <= 0:
                messages.error(request, "Quantity must be greater than 0!")
                return render(request, "accounts/new_product_entry.html", {"form": form})

            stock, created = Stock.objects.get_or_create(
                product=product,
                uom=entry.uom,
                defaults={'quantity': 0, 'created_by': request.user, 'updated_by': request.user}
            )
            stock.quantity += quantity_to_add
            stock.updated_by = request.user
            stock.save()

            messages.success(request, f"Purchase detail added! Stock increased by {quantity_to_add} units.")
            return redirect("manage_stock")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PurchaseDetailForm()

        # Pre-fill purchase if provided in GET parameters
        purchase_id = request.GET.get("purchase_id")
        if purchase_id:
            try:
                purchase = Purchase.objects.get(id=int(purchase_id))
            except (ValueError, Purchase.DoesNotExist):
                pass

    return render(request, "accounts/new_product_entry.html", {"form": form})




# ✅ List Purchase Details
def new_product_list(request):
    entries = PurchaseDetail.objects.all()
    return render(request, "accounts/new_product_list.html", {"entries": entries})


# ✅ Edit Product Entry
def edit_product_entry(request, pk):
    entry = get_object_or_404(PurchaseDetail, pk=pk)

    if request.method == "POST":
        form = PurchaseDetailForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.updated_by = request.user  # ✅ update user
            entry.save()
            return redirect('manage_stock')
    else:
        form = PurchaseDetailForm(instance=entry)

    context = {
        'form': form,
        'entry': entry,
    }
    return render(request, 'accounts/edit_product_entry.html', context)



# ✅ Delete Purchase Detail
def delete_product_entry(request, pk):
    entry = get_object_or_404(PurchaseDetail, pk=pk)
    entry.delete()
    return redirect('new_product_list')



# ✅ Create Purchase
def create_purchase(request): 
    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)

            if not purchase.new_product_entry:
                messages.error(request, "Please select a product.")
                return render(request, 'accounts/create_purchase.html', {'form': form})

            if not purchase.vendor:
                messages.error(request, "Please select a vendor.")
                return render(request, 'accounts/create_purchase.html', {'form': form})

            # ✅ set created_by and updated_by
            if not purchase.pk:
                purchase.created_by = request.user
            purchase.updated_by = request.user

            purchase.save()
            messages.success(request, "Purchase created successfully.")
            return redirect('purchased_list_record') 
    else:
        today = date.today()
        default_required = today + timedelta(days=7)
        form = PurchaseForm(initial={
            'order_date': today,
            'required_date': default_required
        })

    return render(request, 'accounts/create_purchase.html', {'form': form})




def edit_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)

    # Create a formset for line items
    PurchaseItemFormSet = modelformset_factory(
        PurchaseItem,
        form=PurchaseItemForm,
        extra=0,
        can_delete=True
    )

    old_items = {item.id: item.quantity for item in purchase.purchaseitem_set.all()}

    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(
            request.POST,
            queryset=purchase.purchaseitem_set.all()
        )

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                purchase = form.save(commit=False)
                purchase.updated_by = request.user   # ✅ set updated_by
                purchase.save()

                total_amount = 0  # will now sum `price` instead of total_price

                for item_form in formset:
                    if item_form.cleaned_data.get("DELETE"):
                        item = item_form.instance
                        if item.id in old_items:
                            product = item.product
                            product.stock_qty -= old_items[item.id]
                            product.save()
                        item.delete()
                        continue

                    item = item_form.save(commit=False)
                    item.purchase = purchase
                    item.updated_by = request.user   # ✅ set updated_by

                    product = item.product

                    if item.id in old_items:
                        old_qty = old_items[item.id]
                        diff = item.quantity - old_qty
                        product.stock_qty += diff
                    else:
                        product.stock_qty += item.quantity

                    product.save()
                    item.save()

                    total_amount += item.price  # updated field name

                purchase.amount = total_amount  # updated field name
                purchase.status = 'paid' if total_amount > 0 else 'pending'
                purchase.save()

                messages.success(request, "Purchase updated successfully")
                return redirect("purchased_list_record")

    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(queryset=purchase.purchaseitem_set.all())

    return render(
        request,
        "accounts/edit_purchase.html",
        {"form": form, "formset": formset, "purchase": purchase}
    )

    



def delete_purchase(request, pk):
    """Delete a purchase."""
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase.delete()
    return redirect('purchased_list_record')



def purchase_list(request):
    purchase_id = request.GET.get("purchase_id")
    form = PurchaseForm()
    purchase_detail_form = PurchaseDetailForm()
    products_list = []
    purchase = None

    if purchase_id:
        purchase = get_object_or_404(Purchase, pk=purchase_id)

        # Pre-fill products for table
        for entry in purchase.items.all():  # related_name="items"
            products_list.append({
                "product_id": entry.product.id,
                "product_text": entry.product.name,
                "uom": entry.uom,
                "per_unit_price": float(entry.per_unit_price),
                "quantity": float(entry.quantity),
                "price": float(entry.price),
            })

        # Pre-fill purchase form
        form = PurchaseForm(initial={
            "bill_no": purchase.bill_no,
            "order_date": purchase.order_date,
            "warehouse": purchase.warehouse.id if purchase.warehouse else None,
            "purchase_account": purchase.purchase_account.id if purchase.purchase_account else None,
            "vendor": purchase.vendor.id if purchase.vendor else None,
            "amount": purchase.amount,
        })

    context = {
        "form": form,
        "purchase": purchase,
        "new_product_form": purchase_detail_form,
        "products_list_json": json.dumps(products_list),
        "warehouses": Warehouse.objects.all(),
        "accounts": Account.objects.all(),
        "products": Product.objects.all(),
        "vendors": Vendor.objects.all(),
    }
    return render(request, "accounts/purchase_list.html", context)


from django.db.models import F



def save_purchases(request):
    if request.method != "POST":
        return redirect("purchased_list_record")

    purchase_id = request.POST.get("purchase_id")
    product_ids = request.POST.getlist("product[]")
    uoms = request.POST.getlist("uom[]")
    per_prices = request.POST.getlist("per_unit_price[]")
    quantities = request.POST.getlist("quantity[]")

    bill_no = request.POST.get("bill_no")
    order_date_str = request.POST.get("order_date")
    warehouse_id = request.POST.get("warehouse")
    purchase_account_id = request.POST.get("purchase_account")
    vendor_id = request.POST.get("vendor")

    try:
        order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
    except Exception:
        messages.error(request, "Invalid date format")
        return redirect("purchased_list_record")

    if purchase_id:
        purchase = get_object_or_404(Purchase, pk=purchase_id)

        existing_items = list(purchase.items.values(
            'product_id', 'uom', 'per_unit_price', 'quantity'
        ))

        submitted_items = []
        for pid, uom, price, qty in zip_longest(product_ids, uoms, per_prices, quantities, fillvalue=""):
            if not pid:
                continue
            submitted_items.append({
                'product_id': int(pid),
                'uom': uom,
                'per_unit_price': Decimal(price or "0"),
                'quantity': Decimal(qty or "0")
            })

        if existing_items == submitted_items and purchase.bill_no == bill_no and purchase.order_date == order_date \
           and purchase.warehouse_id == (int(warehouse_id) if warehouse_id else None) \
           and purchase.purchase_account_id == (int(purchase_account_id) if purchase_account_id else None) \
           and purchase.vendor_id == (int(vendor_id) if vendor_id else None):
            messages.info(request, "No changes detected. Purchase not updated.")
            return redirect("purchased_list_record")

        for entry in purchase.items.all():
            stock, _ = Stock.objects.get_or_create(
                product=entry.product, uom=entry.uom, defaults={"quantity": 0}
            )
            stock.quantity = F('quantity') - entry.quantity
            stock.save()
            stock.refresh_from_db()

        purchase.items.all().delete()
        StockTransaction.objects.filter(
            transaction_type="purchase",
            transaction_date=purchase.order_date,
            product__in=[i['product_id'] for i in existing_items]
        ).delete()

        purchase.bill_no = bill_no
        purchase.order_date = order_date
        purchase.warehouse_id = warehouse_id if warehouse_id else None
        purchase.purchase_account_id = purchase_account_id if purchase_account_id else None
        purchase.vendor_id = vendor_id if vendor_id else None
        purchase.amount = 0
        purchase.status = "pending"
        purchase.updated_by = request.user
        purchase.save()
    else:
        purchase = Purchase.objects.create(
            bill_no=bill_no,
            order_date=order_date,
            warehouse_id=warehouse_id if warehouse_id else None,
            purchase_account_id=purchase_account_id if purchase_account_id else None,
            vendor_id=vendor_id if vendor_id else None,
            amount=0,
            status="pending",
            created_by=request.user,
        )

    grand_total = Decimal("0.00")
    for i, pid in enumerate(product_ids):
        product = Product.objects.get(pk=int(pid))
        quantity = Decimal(quantities[i]) if quantities[i] else Decimal("0.00")
        per_price = Decimal(per_prices[i]) if per_prices[i] else Decimal("0.00")
        total_price = quantity * per_price
        uom_value = uoms[i] if uoms[i] else "-"

        PurchaseDetail.objects.create(
            purchase=purchase,
            product=product,
            uom=uom_value,
            per_unit_price=per_price,
            quantity=quantity,
            price=total_price,
            created_by=request.user if not purchase_id else None,
            updated_by=request.user if purchase_id else None,
        )

        stock, _ = Stock.objects.get_or_create(
            product=product,
            uom=uom_value,
            defaults={'quantity': 0}
        )
        stock.quantity = F('quantity') + quantity
        stock.save()
        stock.refresh_from_db()

        StockTransaction.objects.create(
            product=product,
            uom=uom_value,
            quantity=quantity,
            transaction_type="purchase",
            transaction_date=order_date,
            created_by=request.user if not purchase_id else None,
            updated_by=request.user if purchase_id else None,
        )

        grand_total += total_price

    purchase.amount = grand_total
    purchase.status = "paid" if grand_total > 0 else "pending"
    purchase.save()

    messages.success(request, "Purchase saved successfully!")
    return redirect("purchased_list_record")


def purchased_list_record(request):
    today = date.today()
    first_day = today.replace(day=1)

    start_date = request.GET.get('start_date', first_day)
    end_date = request.GET.get('end_date', today)

    purchases = Purchase.objects.all().order_by('-id')
    if start_date:
        purchases = purchases.filter(order_date__gte=start_date)
    if end_date:
        purchases = purchases.filter(order_date__lte=end_date)

    return render(request, 'accounts/purchased_list_record.html', {
        'purchases': purchases,
        'first_day': first_day,
        'today': today,
    })



from django.db.models import Sum

def manage_stock(request):
    stock_entries = Stock.objects.all()

    for stock in stock_entries:
        total_purchased = PurchaseDetail.objects.filter(
            product=stock.product,
            uom=stock.uom
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_sold = SaleDetail.objects.filter(
            product=stock.product,
            uom=stock.uom
        ).aggregate(total=Sum('quantity'))['total'] or 0

        adjustment = StockAdjustment.objects.filter(
            product=stock.product,
            uom=stock.uom
        ).aggregate(total=Sum('defective_quantity'))['total'] or 0  # ✅ use actual field name

        stock.quantity = total_purchased - total_sold - adjustment
        stock.updated_by = request.user
        stock.save(update_fields=['quantity', 'updated_by'])

    return render(request, 'accounts/manage_stock.html', {
        'stock_entries': stock_entries
    })


def edit_stock(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.updated_by = request.user   # ✅ who updated
            stock.save()
            messages.success(request, "Stock updated successfully.")
            return redirect('manage_stock')
    else:
        form = StockForm(instance=stock)
    return render(request, 'accounts/edit_stock.html', {'form': form})


def delete_stock(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        stock.delete()
        messages.success(request, "Stock deleted successfully.")
        return redirect('manage_stock')
    return render(request, 'accounts/delete_stock.html', {'stock': stock})



def stock_adjustment(request):
    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.created_by = request.user
            adjustment.save()

            try:
                stock = Stock.objects.get(product=adjustment.product, uom=adjustment.uom)
                stock.quantity -= adjustment.defective_quantity  # ✅ use actual field name
                stock.updated_by = request.user
                stock.save(update_fields=['quantity', 'updated_by'])
                messages.success(request, "Stock adjusted successfully!")
            except Stock.DoesNotExist:
                messages.error(request, "No stock record found for this product and UOM.")

            return redirect("manage_stock")
    else:
        form = StockAdjustmentForm()

    return render(request, "accounts/stock_adjustment.html", {"form": form})





# Add or Edit Sale
def add_sale(request, sale_id=None):
    if sale_id:
        sale = get_object_or_404(Sale, id=sale_id)
        form = SaleForm(instance=sale)
        products_list = [
            {
                "product_id": detail.product.id,
                "product_text": detail.product.name,
                "uom": detail.uom,
                "per_unit_price": float(detail.per_unit_price),
                "quantity": float(detail.quantity),
                "price": float(detail.price),  
            }
            for detail in sale.items.all()
        ]
    else:
        sale = None
        form = SaleForm(initial={"order_date": date.today()})
        products_list = []

    new_product_form = SaleDetailForm()

    context = {
        "form": form,
        "sale": sale,
        "new_product_form": new_product_form,
        "products_list_json": json.dumps(products_list),
        "warehouses": Warehouse.objects.all(),
        "accounts": Account.objects.all(),
        "products": Product.objects.all(),
    }
    return render(request, "accounts/add_sale.html", context)



# Add Sale Details


def add_sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == "POST":
        form = SaleDetailForm(request.POST)
        if form.is_valid():
            detail = form.save(commit=False)
            detail.sale = sale
            detail.price = detail.quantity * detail.per_unit_price

            # --- Track created_by / updated_by ---
            if not detail.id:  # New entry
                detail.created_by = request.user
            detail.updated_by = request.user
            detail.save()

            # Reduce stock
            stock, created = Stock.objects.get_or_create(
                product=detail.product,
                uom=detail.uom,
                defaults={'quantity': 0, 'created_by': request.user}
            )

            if stock.quantity < detail.quantity:
                messages.error(
                    request,
                    f"Not enough stock for {detail.product.name}! Available: {stock.quantity}, Required: {detail.quantity}"
                )
                detail.delete()
            else:
                stock.quantity -= detail.quantity
                stock.updated_by = request.user
                stock.save()

                # Update sale total
                total = SaleDetail.objects.filter(sale=sale).aggregate(amount=Sum('price'))['amount'] or 0
                sale.amount = total
                sale.updated_by = request.user
                sale.save()

                messages.success(request, f"{detail.product.name} added to sale.")

            return redirect('add_sale', sale_id=sale.id)

    else:
        form = SaleDetailForm()

    sale_items = SaleDetail.objects.filter(sale=sale)
    return render(
        request,
        "accounts/add_sale_detail.html",
        {"form": form, "sale": sale, "sale_items": sale_items}
    )





# List all sales
def sale_list(request):
    sales = Sale.objects.select_related('warehouse', 'sale_account').all().order_by('-id')
    return render(request, "accounts/sale_list.html", {"sales": sales})


# Delete sale
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.delete()
    messages.success(request, f"Sale {sale.bill_no} deleted!")
    return redirect('sale_list')


# Save sale from form


from decimal import Decimal
from itertools import zip_longest
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import F
from datetime import datetime


def save_sales(request):
    if request.method != "POST":
        return redirect("sale_list")

    sale_id = request.POST.get("sale_id")
    bill_no = request.POST.get("bill_no")
    order_date_str = request.POST.get("order_date")
    warehouse_id = request.POST.get("warehouse") or None
    sale_account_id = request.POST.get("sale_account") or None

    try:
        order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
    except Exception:
        messages.error(request, "Invalid order date!")
        return redirect("sale_list")

    products = request.POST.getlist("product[]")
    uoms = request.POST.getlist("uom[]")
    per_unit_prices = request.POST.getlist("per_unit_price[]")
    quantities = request.POST.getlist("quantity[]")

    if sale_id:
        sale = get_object_or_404(Sale, id=sale_id)
        existing_items = list(sale.items.values('product_id', 'uom', 'per_unit_price', 'quantity'))
        existing_map = {(item['product_id'], item['uom']): item for item in existing_items}

        submitted_items = []
        for product_id, uom, price, qty in zip_longest(products, uoms, per_unit_prices, quantities, fillvalue=""):
            if not product_id:
                continue
            submitted_items.append({
                'product_id': int(product_id),
                'uom': uom,
                'per_unit_price': Decimal(price or "0"),
                'quantity': Decimal(qty or "0"),
            })

        if existing_items == submitted_items and sale.bill_no == bill_no and sale.order_date == order_date \
           and sale.warehouse_id == (int(warehouse_id) if warehouse_id else None) \
           and sale.sale_account_id == (int(sale_account_id) if sale_account_id else None):
            messages.info(request, "No changes detected. Sale not updated.")
            return redirect("sale_list")

        # Update sale header
        sale.bill_no = bill_no
        sale.order_date = order_date
        sale.warehouse_id = warehouse_id
        sale.sale_account_id = sale_account_id
        sale.amount = 0
        sale.updated_by = request.user
        sale.save()
    else:
        # New sale
        if Sale.objects.filter(bill_no=bill_no).exists():
            messages.error(request, f"Bill No '{bill_no}' already exists!")
            return redirect("add_sale")

        sale = Sale.objects.create(
            bill_no=bill_no,
            order_date=order_date,
            warehouse_id=warehouse_id,
            sale_account_id=sale_account_id,
            amount=0,
            created_by=request.user,
            updated_by=request.user
        )
        existing_map = {}

    total_amount = Decimal("0.00")

    for product_id, uom, price, qty in zip_longest(products, uoms, per_unit_prices, quantities, fillvalue=""):
        if not product_id:
            continue

        product_id_int = int(product_id)
        qty_dec = Decimal(qty or "0")
        price_dec = Decimal(price or "0")
        price_total = qty_dec * price_dec

        key = (product_id_int, uom)
        if key in existing_map:
            old_item = existing_map[key]
            if old_item['quantity'] == qty_dec and old_item['per_unit_price'] == price_dec:
                total_amount += old_item['quantity'] * old_item['per_unit_price']
                continue
            else:
                stock, _ = Stock.objects.get_or_create(
                    product_id=product_id_int,
                    uom=uom,
                    defaults={"quantity": 0}
                )
                stock.quantity = F("quantity") + old_item['quantity']
                stock.save()
                stock.refresh_from_db()
                SaleDetail.objects.filter(sale=sale, product_id=product_id_int, uom=uom).delete()

        # Check stock availability
        stock, _ = Stock.objects.get_or_create(
            product_id=product_id_int,
            uom=uom,
            defaults={"quantity": 0}
        )
        if stock.quantity < qty_dec:
            messages.error(request, f"Not enough stock for {stock.product.name}! Available: {stock.quantity}, Required: {qty_dec}")
            raise transaction.TransactionManagementError("Insufficient stock!")

        # --- Create SaleDetail with user tracking ---
        detail = SaleDetail.objects.create(
            sale=sale,
            product_id=product_id_int,
            uom=uom,
            per_unit_price=price_dec,
            quantity=qty_dec,
            price=price_total,
            created_by=request.user,
            updated_by=request.user
        )
        total_amount += price_total

        # Reduce stock
        Stock.objects.filter(id=stock.id).update(quantity=F("quantity") - qty_dec)

        # Stock transaction
        StockTransaction.objects.create(
            product=detail.product,
            uom=detail.uom,
            quantity=qty_dec,
            transaction_type="sale",
            transaction_date=order_date,
            created_by=request.user,
            updated_by=request.user
        )

    sale.amount = total_amount
    sale.updated_by = request.user
    sale.save()

    if sale_account_id and total_amount > 0:
        AccountDetail.objects.create(
            account_id=sale_account_id,
            date=order_date,
            description=f"Sale: {sale.bill_no}",
            debit=total_amount,
            credit=Decimal("0"),
            created_by=request.user,
            updated_by=request.user
        )

    messages.success(request, "Sale saved successfully!")
    return redirect("sale_list")



    
def new_sale(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user   # ✅ track creator
            sale.save()
            messages.success(request, "Sale created successfully.")
            return redirect("add_sale", sale_id=sale.id)
    else:
        form = SaleForm()

    new_product_form = SaleDetailForm()
    products_list = []

    context = {
        "form": form,
        "new_product_form": new_product_form,
        "products_list_json": "[]",
        "warehouses": Warehouse.objects.all(),
        "accounts": Account.objects.all(),
        "products": Product.objects.all(),
    }
    return render(request, "accounts/add_sale.html", context)




from django.utils.timezone import localtime

def stock_transaction(request):
    transactions = StockTransaction.objects.all().order_by('-transaction_date')
    return render(request, 'accounts/stock_transaction.html', {
        'transactions': transactions
    })


def delete_stock_transaction(request, transaction_id):
    transaction = get_object_or_404(StockTransaction, id=transaction_id)
    transaction.delete()
    messages.success(request, "Transaction deleted successfully!")
    return redirect('stock_transactions') 