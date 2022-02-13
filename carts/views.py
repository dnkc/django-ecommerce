from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
# Create your views here.
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

def _cart_id(request): # _ in front makes it a private function
    cart    =   request.session.session_key
    if not cart:
        cart    =   request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(product = product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the session
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
        cart.save()
    card_item_exists = CartItem.objects.filter(product=product, cart=cart)
    if card_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        # check existing variations (db) and current variations (product variation list), item id (db)
        #if current variation is in existing variation, increase quantity
        ex_var_list = []
        item_id = []
        for item in cart_item:
            item_id.append(item.id)
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))
        if product_variation in ex_var_list:
            # increase the cart item qty
            idx = ex_var_list.index(product_variation)
            found_item_id = item_id[idx]
            item = CartItem.objects.get(product=product, id=found_item_id)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart,
            )
            # create a new card item
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)
            item.save()
    else: 
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart,
        )
        if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
        cart_item.save()
    return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')
    

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total =0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity
    except ObjectDoesNotExist:
        pass
    
    tax = round(((1.13 * total) / 100), 2)
    grand_total = total + tax

    context = {
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'quantity': quantity,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)