# from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from .serializers import MyAddProductSerializer, RegisterSerializer, CustomProductLinkSerializer, QRSerializer, MyProductLinkSerializer, WishlistSerializer, MyAvailabilitySerializer
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.contrib.auth import logout
from oscar.core.loading import get_class, get_model
from rest_framework import generics
from oscarapi.serializers import  ProductSerializer, AvailabilitySerializer, AddProductSerializer, BasketSerializer
import random
from oscarapi.views import ProductPrice, product, ProductDetail
import django
from django.db.models import Q
from oscarapi.basket import operations
User = get_user_model()
product_model = get_model('catalogue', 'product')
# Create your views here.

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

Product = get_model('catalogue', 'Product')

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
        query = self.request.query_params.get('q',None)
        # cat   = self.request.GET.get('cat', None)
        if query is not None:
            qs = qs.filter(
                Q(product_class__name__icontains=query) | Q(title__icontains=query)
            )
        return qs
    def get(self, request, **kwargs):
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
        if type(data) == django.http.request.QueryDict:
            data = int(data.__getitem__('quantity'))
        ser = MyAddProductSerializer(data = {'quantity':data}, context = {'request':request})
        if ser.is_valid():
            product = get_object_or_404(product_model, pk=kwargs['pk'])
            quantity = ser.data['quantity']
            request.basket.add_product(product = product, quantity = quantity)
            return Response(ser.data)
        return Response(
             {'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
