from django import template
from django.db.models import Sum
from django.urls import reverse
from django.db.models.aggregates import Sum

from order.models import ShopCart
from product.models import Category

register = template.Library()


@register.simple_tag
def categorylist():
    return Category.objects.all()


@register.simple_tag
def shopcartcount(userid):

    count = ShopCart.objects.filter(user_id=userid).aggregate(quantity=Sum('quantity'))
    if count['quantity'] is None:
        count['quantity'] = 0
    return count['quantity']

@register.simple_tag
def shopcartcountSession(request):
    cart = request.session.get('cart', {})
    count = 0
    for id, item in cart.items():
        count += item['quantity']
    return count
