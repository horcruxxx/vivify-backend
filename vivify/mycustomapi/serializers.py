from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from oscarapi.utils import overridable, OscarModelSerializer
from oscarapi.serializers import BaseProductSerializer,AddProductSerializer, ProductSerializer, PriceSerializer, product, checkout, AvailabilitySerializer
# from oscar.apps.partner.strategy import Selector
from oscar.core.loading import get_model, get_class
User = get_user_model()
Product = get_model('catalogue', 'Product')
Selector = get_class('partner.strategy', 'Selector')
# Price = get_model('catalogue', 'Price')

class WishlistSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_model('wishlists','Line')
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)
    email    = serializers.EmailField(max_length = 20, validators=[UniqueValidator(queryset=User.objects.all())])
    def create(self, validated_data):
        user = User.objects.create(
            username = validated_data['username'],
            email = validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')
#
# class ProductPriceSerializer(OscarModelSerializer):
#     class Meta:
#         model = Price
#         fields = '__all__'

class CustomProductLinkSerializer(ProductSerializer):
    # strategy = Selector().strategy()
    # product = Product.objects.get(id=1)
    # # f_price = strategy.fetch_for_product(product).price.excl_tax
    # final_price = serializers.DecimalField(max_digits = 10, decimal_places = 2, default = f_price)
    # final_price = PriceSerializer(strategy.fetch_for_product(product).price)
    class Meta(BaseProductSerializer.Meta):
        fields = overridable(
            'OSCARAPI_PRODUCT_FIELDS', default=(
                'url', 'id', 'title', 'product_class',
                'categories', 'images',
            )) #+ ('final_price',)

class MyAvailabilitySerializer(product.ProductLinkSerializer):
    num_available = serializers.SerializerMethodField()
    class Meta(product.ProductLinkSerializer.Meta):
        fields = ('num_available',)
    def get_num_available(self, obj):
        request = self.context.get('request')
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_product(obj).availability,
            context = {'request':request}
        )
        return ser.data

class MyProductLinkSerializer(product.ProductLinkSerializer):
    price = serializers.SerializerMethodField()
    class Meta(product.ProductLinkSerializer.Meta):
        fields = ('price',)
    def get_price(self, obj):
        request = self.context.get('request')
        strategy = Selector().strategy(request=request, user=request.user)
        ser = checkout.PriceSerializer(
            strategy.fetch_for_product(obj).price,
            context = {'request':request}
        )
        return ser.data

class QRSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class MyAddProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    
