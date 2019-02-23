# from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from .serializers import RegisterSerializer, CustomProductLinkSerializer, QRSerializer
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.contrib.auth import logout
from oscar.core.loading import get_class, get_model
from rest_framework import generics
import random
from oscarapi.views import ProductPrice
import django
from django.db.models import Q
User = get_user_model()
# Create your views here.
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

class CustomProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = CustomProductLinkSerializer


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
        query = self.request.GET.get('q',None)
        # cat   = self.request.GET.get('cat', None)
        if query is not None:
            qs = qs.filter(
                Q(product_class__name__icontains=query) | Q(title__icontains=query)
            )
        return qs

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
