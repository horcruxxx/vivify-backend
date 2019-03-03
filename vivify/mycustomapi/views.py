# from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status,response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from .serializers import MyMostViewedSerializer,MyRecentlyViewedSerializer, MyAddProductSerializer, RegisterSerializer, CustomProductLinkSerializer, QRSerializer, MyProductLinkSerializer, WishlistSerializer, MyAvailabilitySerializer
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.contrib.auth import logout
from oscar.core.loading import get_class, get_model, get_classes
from rest_framework import generics
from oscarapi.serializers import  (ProductSerializer, AvailabilitySerializer, AddProductSerializer,
                                    BasketSerializer,BasketLineSerializer)
import random
from difflib import SequenceMatcher
from oscarapi.signals import oscarapi_post_checkout
from oscarapi.basket.operations import request_allows_access_to_basket
from oscarapi.views import ProductPrice, product, ProductDetail, LineList, CheckoutView, OrderList, OrderLineList
import django
from django.db.models import Q
from oscarapi.basket import operations
from oscarapi.views.utils import parse_basket_from_hyperlink
from oscar.apps.analytics.receivers import _update_counter, _record_products_in_order, _record_user_order
Product = get_model('catalogue', 'Product')
UserSearch, UserRecord, ProductRecord, UserProductView = get_classes(
    'analytics.models', ['UserSearch', 'UserRecord', 'ProductRecord',
    'UserProductView'])

User = get_user_model()
product_model = get_model('catalogue', 'product')
# Create your views here.
Order = get_model('order', 'Order')

class MyMostViewed(generics.ListAPIView):
    queryset = ProductRecord.objects.all()
    serializer_class = MyMostViewedSerializer
    def get_queryset(self):
        qs = ProductRecord.objects.all().order_by('-num_views')
        query = self.request.query_params.get('cat',None)
        # fulltext = self.request.query_params.get('q', None)
        # cat   = self.request.GET.get('cat', None)
        if query is not None:
            qs = qs.filter(
                Q(product_class__name__icontains=query) | Q(title__icontains=query)
            )
        return qs

class MyRecentlyViewed(generics.ListAPIView):
    queryset = UserProductView.objects.all()
    serializer_class = MyRecentlyViewedSerializer
    def get_queryset(self):
        email = self.request.query_params.get('email',None)
        user = User.objects.filter(email=email).first()
        qs = UserProductView.objects.filter(user=user).order_by('-date_created')
        query = self.request.query_params.get('cat',None)
        # fulltext = self.request.query_params.get('q', None)
        # cat   = self.request.GET.get('cat', None)
        if query is not None:
            qs = qs.filter(
                Q(product_class__name__icontains=query) | Q(title__icontains=query)
            )
        return qs


class MyOrderList(OrderList):
    permission_classes = [
        permissions.AllowAny
        ]
    def get_queryset(self):
        print('hello')
        qs = Order.objects.all()
        email = self.request.query_params.get('email', None)
        print(email)
        if email is not None:
            self.request.user = User.objects.filter(email=email).first()
            return qs.filter(user=self.request.user)
        return qs

class MyOrderLineList(OrderLineList):
    permission_classes = [
        permissions.AllowAny
        ]
    def get(self, request, pk=None, format=None):
        email = request.query_params.get('email', None)
        print(email)
        if email is not None:
            request.user = User.objects.filter(email=email).first()
        print(request.user)
        if pk is not None:
            self.queryset = self.queryset.filter(
                order__id=pk, order__user=request.user)
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(OrderLineList, self).get(request, format)
# class MyProductRecord(generics.ListAPIView):
#     queryset = ProductRecord.objects.all().order_by('-')
#     serializer_class = MyProductRecordSerializer
#     def get():
#
class MyCheckoutView(CheckoutView):
     def post(self, request, format=None):
        # TODO: Make it possible to create orders with options.
        # at the moment, no options are passed to this method, which means they
        # are also not created.
        email = request.query_params.get('email', None)
        print(email)
        if email is not None:
            request.user = User.objects.filter(email=email).first()

        basket = parse_basket_from_hyperlink(request.data, format)

        if not request_allows_access_to_basket(request, basket):
            return response.Response(
                "Unauthorized", status=status.HTTP_401_UNAUTHORIZED)

        c_ser = self.serializer_class(
            data=request.data, context={'request': request})

        if c_ser.is_valid():
            order = c_ser.save()
            _record_products_in_order(order)
            _record_user_order(request.user, order)
            basket.freeze()
            o_ser = self.order_serializer_class(
                order, context={'request': request})

            resp = response.Response(o_ser.data)

            oscarapi_post_checkout.send(
                sender=self, order=order, user=request.user,
                request=request, response=resp)
            return resp

        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)

class MyLineList(LineList):
    def get(self, request, pk=None, format=None):
        if pk is not None:
            email = request.query_params.get('email', None)
            print(email)
            if email is not None:
                request.user = User.objects.filter(email=email).first()
            basket = self.check_basket_permission(request, pk)
            prepped_basket = operations.assign_basket_strategy(basket, request)
            self.queryset = prepped_basket.all_lines()
            self.serializer_class = BasketLineSerializer

        return super(MyLineList, self).get(request, format)

class MyBasketView(APIView):
    serializer_class = BasketSerializer
    def get(self, request, format=None):
        email = request.query_params.get('email',None)
        print(email)
        if email is not None:
            request.user = User.objects.filter(email=email).first()
        basket = operations.get_basket(request)
        ser = self.serializer_class(basket, context={'request': request})
        return Response(ser.data)

class WishlistView(CreateAPIView):
    model = get_model('wishlists','Line')
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = WishlistSerializer

class RegisterView(CreateAPIView):
    model = User
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = RegisterSerializer
    # def post(self, request, format=None):
    #     serialized = RegisterSerializer(data=request.data)
    #     if serialized.is_valid():
    #         User.objects.create_user(
    #             serialized.data['username'],
    #             serialized.data['password']
    #         )
    #         return Response(serialized.data, status=status.HTTP_201_CREATED)
    #     else:
    #         return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)



class MyProductDetail(ProductDetail):
    queryset = Product.objects.all()
    def get_queryset(self):
        queryset = Product.objects.filter(pk=self.kwargs['pk'])
        return queryset
    def get(self, request, **kwargs):
        qs = self.get_queryset()
        context = {'request':request}
        qs_ser = ProductSerializer(qs, many=True, context = context)
        price_ser = MyProductLinkSerializer(qs, many=True, context = context)
        avail_ser = MyAvailabilitySerializer(qs, many=True, context = context)
        response = qs_ser.data
        response[0]['price'] = price_ser.data[0]['price']
        response[0]['availability'] = avail_ser.data[0]['num_available']
        print(list(qs)[0])

        email = request.query_params.get('email', None)
        if email is not None:
            user = User.objects.filter(email=email).first()
            UserProductView.objects.create(user=user, product=list(qs)[0])
            if user and user.is_authenticated:
                _update_counter(UserRecord, 'num_product_views', {'user': user})

        _update_counter(ProductRecord, 'num_views', {'product':list(qs)[0]})
        return Response(response)


class CustomProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = CustomProductLinkSerializer
    paginate_by = 10
    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent products can
        be selected separately, eg::
            http://127.0.0.1:8000/api/products/?structure=standalone
        or::
            http://127.0.0.1:8000/api/products/?structure=parent
        """
        qs = super(CustomProductList, self).get_queryset()
        structure = self.request.query_params.get('structure')
        if structure is not None:
            return qs.filter(structure=structure)
        query = self.request.query_params.get('cat',None)
        fulltext = self.request.query_params.get('q', None)
        # cat   = self.request.GET.get('cat', None)
        if query is not None:
            qs = qs.filter(
                Q(product_class__name__icontains=query) | Q(title__icontains=query)
            )
            return qs
        elif fulltext is not None:
            query = []
            p_query = []

            title = Product.objects.all()
            product_class = Product.objects.all()
            cat = Product.objects.all()

            titles = [x.title for x in title]
            product_classes = [x.product_class for x in product_class]
            cats = [x.categories for x in cat if x.categories is not None]


            THRESHOLD = .5
            for text in fulltext.split():
                for title in titles:
                    title = str(title)
                    score = SequenceMatcher(None, title.lower(), text.lower()).ratio()
                    if score == 1:
                        # Perfect Match for name
                        p_query += Product.objects.filter(Q(title__icontains=title))
                    elif score >= THRESHOLD or text.lower() in title.lower():
                        query += (Product.objects.filter(Q(title__icontains=title)))

                for product_class in product_classes:
                    product_class = str(product_class)
                    score = SequenceMatcher(None, product_class.lower(), text.lower()).ratio()
                    if score == 1:
                        p_query += Product.objects.filter(Q(product_class__name__icontains=product_class))
                    elif score >= THRESHOLD or text.lower() in product_class.lower():
                        query += (Product.objects.filter(Q(product_class__name__icontains=product_class)))

            if len(p_query) > 0:
                query = p_query

            # print(query)

            return query
        return qs


    def get(self, request, **kwargs):

        # print(user)
        products = self.get_queryset()
        context = {
            'request' : request
        }
        page = self.paginate_queryset(products)
        if page is not None:
            prod_ser = CustomProductLinkSerializer(page, many=True, context = context)
            price_ser = MyProductLinkSerializer(page, many=True, context = context)
            response = prod_ser.data
            for i in range(len(response)):
                response[i]['price'] = price_ser.data[i]['price']
            return self.get_paginated_response(response)

        prod_ser = CustomProductLinkSerializer(products, many=True, context = context)
        price_ser = MyProductLinkSerializer(products, many=True, context = context)
        response = prod_ser.data
        for i in range(len(response)):
            response[i]['price'] = price_ser.data[i]['price']

        return Response(response)



class ProductList(product.ProductList):
    queryset = Product.objects.all()
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        price_ser = MyProductLinkSerializer(qs, many=True, context = {'request':request})
        return Response(price_ser.data)




class QR(object):
    def __init__(self, id):
        self.id = id

qr_object = QR(id = 10)

class QRView(APIView):
    def get(self, request, format=None):
        qr_object.id = random.randint(100,999)
        serializer = QRSerializer(qr_object)
        return Response(serializer.data)
    def post(self, request, format = None):
        a = request.data
        if type(request.data) == django.http.request.QueryDict:
            a = int(a.__getitem__('id'))
        serializer = QRSerializer(data = {'id' : a})
        if serializer.is_valid() and a == qr_object.id:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class MyAddProductView(CreateAPIView):
    serializer_class = MyAddProductSerializer
    def post(self, request, *args, **kwargs):
        data = request.data
        print(request.user)
        print(request.data)
        if type(data) == django.http.request.QueryDict:
            data = int(data.__getitem__('quantity'))
            print("---------hello")
        email = request.data.__getitem__('email')
        print(email)
        print(data)
        ser = MyAddProductSerializer(data = {'quantity':data}, context = {'request':request})
        if ser.is_valid():
            user = User.objects.filter(email=email).first()
            # user = ser.instance

            product = get_object_or_404(product_model, pk=kwargs['pk'])
            quantity = ser.data['quantity']
            request.basket.add_product(product = product, quantity = quantity)
            request.basket.owner = user
            # print(request.user)
            request.basket.save()
            _update_counter(ProductRecord, 'num_basket_additions', {'product':product}, quantity)
            if user and user.is_authenticated:
                _update_counter(UserRecord, 'num_basket_additions', {'user': user})
            return Response(ser.data)
        return Response(
             {'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
