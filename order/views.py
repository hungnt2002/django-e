from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

# Create your views here.
from django.utils.crypto import get_random_string

from order.models import ShopCart, ShopCartForm, OrderForm, Order, OrderProduct
from product.models import Category, Product, Variants
from user.models import UserProfile


def index(request):
    return HttpResponse("Order Page")

def addtoshopcart(request,id):
    url = request.META.get('HTTP_REFERER')
    current_user = request.user 
    product= Product.objects.get(pk=id)
    id = str(id)

    variantid = None
    if(not request.user.is_authenticated):
        cart = request.session.get('cart', {})  # Lấy giỏ hàng từ session
        control = 0
        
        if cart:
            checkinproduct = False
            if id in cart:
                checkinproduct = True
                
            if checkinproduct:
                control = 1 # sản phẩm trong giỏ hàng
            else:
                control = 0 # Sản phẩm không trong giỏ hàng
        
        if request.method == 'POST':

            if control==1: # Cập nhật giỏ hàng
                cart[id]['quantity'] += int(request.POST.get('quantity'))
            else : # Thêm vào giỏ hàng
                cart[id] = {
                    'quantity': 1,
                    'nameProduct': product.title,
                    'price': float(product.price),
                    'image': product.image.url,
                    'slug': product.slug,
                }  # Thêm sản phẩm mới vào giỏ hàng
            
            request.session['cart'] = cart  # Lưu giỏ hàng vào session
                    
            messages.success(request, "Product added to Shopcart ")
            return HttpResponseRedirect(url)

        else: # method GET
            if control == 1:  # Cập nhật giỏ hàng
                print(request.GET.get('quantity'))
                cart[id]['quantity'] += 1
            else:  # Thêm vào giỏ hàng
                cart[id] = {
                'quantity': 1,
                'nameProduct': product.title,
                'price': float(product.price),
                'image': product.image.url,
                'slug': product.slug,
            }  # Thêm sản phẩm mới vào giỏ hàng
            
            request.session['cart'] = cart  # Lưu giỏ hàng vào session
            messages.success(request, "Product added to Shopcart")
            return HttpResponseRedirect(url)
            
    else: # Truờng hợp đăng nhập (Không dùng session)
        if product.variant != 'None':
            variantid = request.POST.get('variantid') 
            checkinvariant = ShopCart.objects.filter(variant_id=variantid, user_id=current_user.id)
            if checkinvariant:
                control = 1 # sản phẩm trong giỏ hàng
            else:
                control = 0 # Sản phẩm không trong giỏ hàng
        else:
            checkinproduct = ShopCart.objects.filter(product_id=id, user_id=current_user.id)
            if checkinproduct:
                control = 1 # sản phẩm trong giỏ hàng
            else:
                control = 0 # Sản phẩm không trong giỏ hàng

        if request.method == 'POST':  # if there is a post
            form = ShopCartForm(request.POST)
            if form.is_valid():
                if control==1: # Cập nhật giỏ hàng
                    if product.variant == 'None':
                        data = ShopCart.objects.get(product_id=id, user_id=current_user.id)
                    else:
                        data = ShopCart.objects.get(product_id=id, variant_id=variantid, user_id=current_user.id)
                    data.quantity += form.cleaned_data['quantity']
                    data.save() 
                else : # Thêm vào giỏ hàng
                    data = ShopCart()
                    data.user_id = current_user.id
                    data.product_id =id
                    if variantid:
                        data.variant_id = variantid
                    data.quantity = form.cleaned_data['quantity']
                    data.save()
            messages.success(request, "Product added to Shopcart ")
            return HttpResponseRedirect(url)

        else: 
            if control == 1:  
                print(current_user.id)
                data = ShopCart.objects.get(product_id=id, user_id=current_user.id)
                data.quantity += 1
                data.save()  #
            else:  
                data = ShopCart()  
                data.user_id = current_user.id
                data.product_id = id
                data.quantity = 1
                data.variant_id = None
                data.save()  #
            messages.success(request, "Product added to Shopcart")
            return HttpResponseRedirect(url)

def shopcart(request):
    if not request.user.is_authenticated:
        cart = request.session.get('cart', {})  # Lấy giỏ hàng từ session
        total = 0

        # Tính tổng giá tiền của giỏ hàng
        for id, item in cart.items():
            total += item['price'] * item['quantity']
            item['unitTotal'] = item['price'] * item['quantity']
        category = Category.objects.all()

        context={
                'category':category,
                'total': total,
                'cart': cart
                }
        return render(request,'shopcart_products.html',context)
        
    else:
        current_user = request.user 
        shopcart = ShopCart.objects.filter(user_id=current_user.id)
        total=0
        for rs in shopcart:
            total += rs.product.price * rs.quantity

        category = Category.objects.all()

        context={'shopcart': shopcart,
                'category':category,
                'total': total
                }
        return render(request,'shopcart_products.html',context)

def deletefromcart(request,id):
    cart = request.session.get('cart', {})  # Lấy giỏ hàng từ session
    id = str(id)
    if id in cart:
        del cart[id]  # Xóa sản phẩm khỏi giỏ hàng

    request.session['cart'] = cart  # Lưu giỏ hàng vào session

    if(request.user.is_authenticated):
        ShopCart.objects.filter(id=id).delete()
    
    messages.success(request, "Your item deleted from Shopcart.")
    return redirect('/shopcart')



@login_required(login_url='/login')
def orderproduct(request):
    category = Category.objects.all()
    current_user = request.user
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    for rs in shopcart:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

    if request.method == 'POST': 
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.phone = form.cleaned_data['phone']
            data.user_id = current_user.id
            data.total = total
            ordercode= get_random_string(5).upper()
            data.code =  ordercode
            data.save() #


            for rs in shopcart:
                detail = OrderProduct()
                detail.order_id     = data.id
                detail.product_id   = rs.product_id
                detail.user_id      = current_user.id
                detail.quantity     = rs.quantity
                if rs.product.variant == 'None':
                    detail.price    = rs.product.price
                else:
                    detail.price = rs.variant.price
                detail.variant_id   = rs.variant_id
                detail.amount        = rs.amount
                detail.save()
                
                if  rs.product.variant=='None':
                    product = Product.objects.get(id=rs.product_id)
                    product.amount -= rs.quantity
                    product.save()
                else:
                    variant = Variants.objects.get(id=rs.product_id)
                    variant.quantity -= rs.quantity
                    variant.save()
            

            ShopCart.objects.filter(user_id=current_user.id).delete()
            request.session['cart_items']=0
            messages.success(request, "Your Order has been completed. Thank you ")
            return render(request, 'Order_Completed.html',{'ordercode':ordercode,'category': category})
        else:
            messages.warning(request, form.errors)
            return HttpResponseRedirect("/order/orderproduct")

    form= OrderForm()
    profile = UserProfile.objects.get(user_id=current_user.id)
    context = {'shopcart': shopcart,
               'category': category,
               'total': total,
               'form': form,
               'profile': profile,
               }
    return render(request, 'Order_Form.html', context)