from django.urls import path
from .views import (
    # Authentication
    signup_view, verify_otp_view, login_view, logout_view,

    # Accounts & Ledger
    add_account, account_list, edit_account, delete_account,
    account_detail_view, account_entries_view,
    edit_entry, delete_entry, transaction_view,
    general_ledger_summary_view, trial_balance_view,

    # Categories & Products
    add_category, manage_categories, product_category_list,
    manage_subcategories, add_subcategory,
    product_list_view, add_product_view,

    # Warehouses
    warehouse_list, add_warehouse, edit_warehouse, delete_warehouse,

    # Inventory Entries & Purchases
    new_product_entry, new_product_list, 
    create_purchase, purchase_list,  edit_purchase, manage_stock, 
    delete_purchase, delete_product_entry, edit_product_entry, purchased_list_record, 
    save_purchases, purchased_list_record, stock_adjustment, edit_stock, delete_stock,
    sale_list, add_sale, add_sale_detail, delete_sale, save_sales, new_sale, stock_transaction,
    delete_stock_transaction,
)

urlpatterns = [
    # ---------------- AUTH ----------------
    path('signup/', signup_view, name='signup'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # ---------------- ACCOUNTS ----------------
    path('accounts/add/', add_account, name='add_account'),
    path('accounts/', account_list, name='account_list'),
    path('accounts/edit/<int:account_id>/', edit_account, name='edit_account'),
    path('accounts/delete/<int:account_id>/', delete_account, name='delete_account'),

    # ---------------- ENTRIES & TRANSACTIONS ----------------
    path('entries/add/', account_detail_view, name='account_detail'),
    path('entries/', account_entries_view, name='account_entries'),
    path('entries/edit/<int:entry_id>/', edit_entry, name='edit_entry'),
    path('entries/delete/<int:entry_id>/', delete_entry, name='delete_entry'),
    path('transactions/', transaction_view, name='transaction_view'),

    # ---------------- LEDGER ----------------
    path('general-ledger/', general_ledger_summary_view, name='general_ledger_summary'),
    path('trial-balance/', trial_balance_view, name='trial_balance'),

    # ---------------- CATEGORIES ----------------
    path('categories/', manage_categories, name='manage_categories'),
    path('categories/add/', add_category, name='add_category'),
    path('product-categories/', product_category_list, name='product_category_list'),

    # ---------------- SUBCATEGORIES ----------------
    path('subcategories/', manage_subcategories, name='manage_subcategories'),
    path('subcategories/add/', add_subcategory, name='add_subcategory'),

    # ---------------- PRODUCTS ----------------
    path('products/', product_list_view, name='product_list'),
    path('products/add/', add_product_view, name='add_product'),

    # ---------------- WAREHOUSES ----------------
    path('warehouses/', warehouse_list, name='warehouse_list'),
    path('warehouses/add/', add_warehouse, name='add_warehouse'),
    path('warehouses/edit/<int:pk>/', edit_warehouse, name='edit_warehouse'),
    path('warehouses/delete/<int:pk>/', delete_warehouse, name='delete_warehouse'),

    # ---------------- INVENTORY ----------------
    path('inventory/new-product/', new_product_entry, name='new_product_entry'),
    path('inventory/new-product/list/', new_product_list, name='new_product_list'),

    # ---------------- PURCHASES ----------------
    path('purchases/add/', create_purchase, name='create_purchase'),
    path('purchases/', purchase_list, name='purchase_list'),
    path('purchases/edit/<int:pk>/', edit_purchase, name='edit_purchase'),
    path('purchases/delete/<int:pk>/', delete_purchase, name='delete_purchase'),
    path('inventory/new-product/edit/<int:pk>/', edit_product_entry, name='edit_product_entry'),
    path('inventory/new-product/delete/<int:pk>/', delete_product_entry, name='delete_product_entry'),
    path('purchased-list/', purchased_list_record, name='purchased_list_record'),
    path('purchases/save-batch/', save_purchases, name='save_purchases'),
    path('purchases/records/', purchased_list_record, name='purchased_list_record'),

    path("stock/", manage_stock, name="manage_stock"),
    path("stock-adjustment/",stock_adjustment, name="stock_adjustment"),

    path('stock/edit/<int:pk>/', edit_stock, name='edit_stock'),
    path('stock/delete/<int:pk>/', delete_stock, name='delete_stock'),

    #----------------------------sales--------------------------

    path('sales/', sale_list, name='sale_list'),
    path('sales/add/',add_sale, name='add_sale'),
    path('sales/add/<int:sale_id>/',add_sale, name='add_sale'),
    path('sales/add/', sale_list, name='new_sale'),
    path('sales/save/', save_sales, name='save_sales'),
    path('sales/<int:sale_id>/details/add/', add_sale_detail, name='sale_detail_add'),
    path('sales/<int:sale_id>/delete/', delete_sale, name='delete_sale'),

    path("stock/transactions/", stock_transaction, name="stock_transaction"),

    path('stock/transaction/delete/<int:transaction_id>/', delete_stock_transaction, name='delete_stock_transaction'),


]
