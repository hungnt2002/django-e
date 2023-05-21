import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, F
from django.db.models.functions import Concat
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, request
from django.shortcuts import render

# Create your views here.
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation

from home.forms import SearchForm
from home.models import Setting, ContactForm, ContactMessage, FAQ
from mysite import settings
from product.models import Category, Product, Images, Comment, Variants


def index(request):

    setting = Setting.objects.get(pk=1)
    products_latest = Product.objects.all().order_by('-id')[:4]  # last 4 products
    products_slider = Product.objects.all().order_by('id')[:4]  #first 4 products
    products_picked = Product.objects.all().order_by('?')[:4]   #Random selected 4 products
    category = Category.objects.all()
    page="home"
    context={'setting':setting,
             'page':page,
             'products_slider': products_slider,
             'products_latest': products_latest,
             'products_picked': products_picked,
             'category':category
             }
    
    return render(request,'index.html',context)

def aboutus(request):
    setting = Setting.objects.get(pk=1)
    context={'setting':setting}
    return render(request, 'about.html', context)

def contactus(request):
    if request.method == 'POST': # check post
        form = ContactForm(request.POST)
        if form.is_valid():
            data = ContactMessage() #create relation with model
            data.name = form.cleaned_data['name'] # get form input data
            data.email = form.cleaned_data['email']
            data.subject = form.cleaned_data['subject']
            data.message = form.cleaned_data['message']
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()  #save data to table
            messages.success(request,"Your message has ben sent. Thank you for your message.")
            return HttpResponseRedirect('/contact')

    setting = Setting.objects.get(pk=1)
    form = ContactForm
    context={'setting':setting,'form':form  }
    return render(request, 'contactus.html', context)

def category_products(request,id,slug):
    catdata = Category.objects.get(pk=id)
    products = Product.objects.filter(category_id=id)

    context={'products': products,
             'catdata':catdata }
    return render(request,'category_products.html',context)

def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query'] 
            catid = form.cleaned_data['catid']
            if catid==0:
                products=Product.objects.filter(title__icontains=query)  #SELECT * FROM product WHERE title LIKE '%query%'
            else:
                products = Product.objects.filter(title__icontains=query,category_id=catid)

            category = Category.objects.all()
            context = {'products': products, 'query':query,
                       'category': category }
            return render(request, 'search_products.html', context)

    return HttpResponseRedirect('/')

def product_detail(request,id,slug):
    category = Category.objects.all()
    product = Product.objects.get(pk=id)
    images = Images.objects.filter(product_id=id)
    comments = Comment.objects.filter(product_id=id)
    context = {'product': product,'category': category,
               'images': images, 'comments': comments,
               }
    if product.variant !="None": # Product have variants
        if request.method == 'POST': #if we select color
            variant_id = request.POST.get('variantid')
            variant = Variants.objects.get(id=variant_id) #selected product by click color radio
            sizes = Variants.objects.raw('SELECT * FROM  product_variants  WHERE product_id=%s GROUP BY size_id',[id])
        else:
            variants = Variants.objects.filter(product_id=id)
            sizes = Variants.objects.raw('SELECT * FROM  product_variants  WHERE product_id=%s GROUP BY size_id',[id])
            variant =Variants.objects.get(id=variants[0].id)
        context.update({'sizes': sizes,
                        'variant': variant
                        })
    return render(request,'product_detail.html',context)


def faq(request):
    faq = FAQ.objects.filter(status="True").order_by("ordernumber")

    context = {
        'faq': faq,
    }
    return render(request, 'faq.html', context)