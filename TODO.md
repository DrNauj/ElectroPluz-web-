# TODO: Modify Store to Display Only Categories with Active Products

## Tasks
- [x] Modify the categories query in `ElectroPlus-Gateway-New/storefront/views.py` to filter categories with active products
- [ ] Test the change by running the Django server and verifying categories without active products are not displayed

## Details
- Change `categories = Category.objects.all()` to `categories = Category.objects.filter(product__is_active=True).distinct()`
- This ensures only categories with at least one active product are shown in the sidebar.
