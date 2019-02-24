from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from oscarapi.utils import overridable, OscarModelSerializer
from oscarapi.serializers import BaseProductSerializer, ProductSerializer, PriceSerializer
from oscar.apps.partner.strategy import Selector
from oscar.core.loading import get_model
User = get_user_model()
Product = get_model('catalogue', 'Product')
# Price = get_model('catalogue', 'Price')
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
                'categories', 'images', 'price',
            )) #+ ('final_price',)


class QRSerializer(serializers.Serializer):
    id = serializers.IntegerField()
