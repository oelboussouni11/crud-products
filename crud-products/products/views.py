# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Auth
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required

# CSV / IO
from django.http import HttpResponse
from django.db import transaction
import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

from .models import Product
from .forms import ProductForm, CSVUploadForm


# ---------- Landing ----------
def landing(request):
    # Option A: redirect authenticated users away from landing
    if request.user.is_authenticated:
        return redirect('product_list')
    return render(request, 'landing.html')


# ---------- Products ----------
@login_required
def product_list(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '-updated')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', '10')

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    per_page = max(1, min(per_page, 50))

    sort_map = {
        'name': 'name', '-name': '-name',
        'price': 'price', '-price': '-price',
        'stock': 'stock', '-stock': '-stock',
        'updated': 'updated_at', '-updated': '-updated_at',
        'created': 'created_at', '-created': '-created_at',
    }
    order_by = sort_map.get(sort, '-updated_at')

    qs = Product.objects.filter(owner=request.user)
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(category__icontains=q) |
            Q(description__icontains=q)
        )
    qs = qs.order_by(order_by)

    paginator = Paginator(qs, per_page)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'index.html', {
        'products': products,
        'q': q,
        'sort': sort,
        'per_page': per_page,
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    return render(request, 'product_detail.html', {'product': product})


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            messages.success(request, f'“{product.name}” created.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form, 'product': None})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'“{product.name}” updated.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'product_form.html', {'form': form, 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'“{name}” deleted.')
        return redirect('product_list')
    return render(request, 'product_delete.html', {'product': product})


# ---------- Auth ----------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    form = AuthenticationForm(request, data=request.POST or None)
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        return redirect(next_url or 'product_list')
    return render(request, 'login.html', {'form': form, 'next': next_url})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, "Welcome! Your account is ready.")
        return redirect('product_list')
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        messages.success(request, "Logged out.")
        return redirect('landing')
    return redirect('product_list')


# ---------- CSV ----------
@login_required
def product_export_csv(request):
    """Download current user's products as CSV."""
    qs = Product.objects.filter(owner=request.user).order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'category', 'price', 'stock',
                    'description', 'image_url', 'created_at', 'updated_at'])
    for p in qs:
        writer.writerow([
            p.name,
            p.category,
            str(p.price),
            p.stock,
            (p.description or "").replace('\r', ' ').replace('\n', ' '),
            p.image_url,
            p.created_at.isoformat(timespec='seconds'),
            p.updated_at.isoformat(timespec='seconds'),
        ])
    return response


@login_required
def product_csv_template(request):
    """
    Download a CSV template (headers only).
    Add ?sample=1 to include 3 sample rows.
    """
    include_sample = request.GET.get('sample') == '1'
    response = HttpResponse(content_type='text/csv')
    fname = 'products_template_sample.csv' if include_sample else 'products_template.csv'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    w = csv.writer(response)
    w.writerow(['name', 'category', 'price',
               'stock', 'description', 'image_url'])
    if include_sample:
        w.writerow(['Atlas Tee', 'T-Shirts', '25.00', '42',
                   'Soft cotton t-shirt', 'https://example.com/tee.jpg'])
        w.writerow(['Dune Hoodie', 'Hoodies',
                   '59.00', '12', 'Comfy hoodie', ''])
        w.writerow(['Zellige Cap', 'Accessories', '19.00', '73',
                   'Adjustable cap', 'https://example.com/cap.jpg'])
    return response


@login_required
def product_import_csv(request):
    """
    Upload a CSV with columns: name,category,price,stock,description,image_url
    - Upserts by (owner, name).
    - If 'strict' is checked, abort entire import when any row has errors.
    """
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['file']
            strict = form.cleaned_data.get('strict', False)

            data = upload.read().decode('utf-8', errors='ignore')
            reader = csv.DictReader(StringIO(data))

            required = {'name', 'price', 'stock'}
            headers = {h.strip() for h in (reader.fieldnames or [])}
            missing = required - headers
            if missing:
                messages.error(
                    request, f"Missing required columns: {', '.join(sorted(missing))}")
                return redirect('product_import_csv')

            rows = list(reader)
            errors = []
            clean_rows = []

            # Validate all rows first
            for idx, row in enumerate(rows, start=2):  # header is line 1
                name = (row.get('name') or '').strip()
                category = (row.get('category') or '').strip()
                description = (row.get('description') or '').strip()
                image_url = (row.get('image_url') or '').strip()
                price_str = (row.get('price') or '').replace(',', '').strip()
                stock_str = (row.get('stock') or '').strip()

                row_errors = []
                if not name:
                    row_errors.append("name is required")

                try:
                    price = Decimal(price_str)
                    if price < 0:
                        row_errors.append("price must be ≥ 0")
                except (InvalidOperation, ValueError):
                    row_errors.append(f"invalid price '{price_str}'")

                try:
                    stock = int(stock_str)
                    if stock < 0:
                        row_errors.append("stock must be ≥ 0")
                except ValueError:
                    row_errors.append(f"invalid stock '{stock_str}'")

                if row_errors:
                    errors.append(f"Row {idx}: " + "; ".join(row_errors))
                else:
                    clean_rows.append({
                        'name': name,
                        'category': category,
                        'price': price,
                        'stock': stock,
                        'description': description,
                        'image_url': image_url,
                    })

            if strict and errors:
                preview = "; ".join(errors[:5])
                more = "" if len(errors) <= 5 else f" (+{len(errors)-5} more)"
                messages.error(
                    request, f"Import aborted: {len(errors)} error(s). {preview}{more}")
                return redirect('product_import_csv')

            # Proceed (lenient: skip bad rows; strict: already ensured no errors)
            created = updated = 0
            skipped = 0 if strict else (len(rows) - len(clean_rows))

            with transaction.atomic():
                for r in clean_rows:
                    obj, was_created = Product.objects.update_or_create(
                        owner=request.user,
                        name=r['name'],
                        defaults={
                            'category': r['category'],
                            'price': r['price'],
                            'stock': r['stock'],
                            'description': r['description'],
                            'image_url': r['image_url'],
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

            msg = f"Import complete — {created} created, {updated} updated"
            if not strict:
                msg += f", {skipped} skipped"
            messages.success(request, msg + ".")
            return redirect('product_list')
    else:
        form = CSVUploadForm()

    return render(request, 'import_csv.html', {'form': form})
