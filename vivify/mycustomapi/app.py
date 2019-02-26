from oscarapi.app import RESTApiApplication
from django.urls import path

from . import views

app_name = 'mycustomapi'

class MyRESTApiApplication(RESTApiApplication):

    def get_urls(self):
        urls = [
            path('register/',views.RegisterView.as_view(), name='register'),
            path('custom_products/', views.CustomProductList.as_view(), name='custom_products'),
            path('qr/', views.QRView.as_view(), name = 'qr'),
            path('prices/', views.ProductList.as_view(), name = 'price'),
            path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
            path('products/<int:pk>/', views.MyProductDetail.as_view(), name='my_product_detail'),
            path('basket/myadd/<int:pk>/', views.MyAddProductView.as_view(), name='my_add_product')
        ]

        return urls + super(MyRESTApiApplication, self).get_urls()

application = MyRESTApiApplication()
