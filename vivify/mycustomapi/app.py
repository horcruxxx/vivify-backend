from oscarapi.app import RESTApiApplication
from django.urls import path

from . import views

app_name = 'mycustomapi'

class MyRESTApiApplication(RESTApiApplication):

    def get_urls(self):
        urls = [
            path('register/',views.RegisterView.as_view(), name='register'),
            path('custom_products/', views.CustomProductList.as_view(), name='custom_products'),
            path('qr/', views.QRView.as_view(), name = 'qr')
        ]

        return urls + super(MyRESTApiApplication, self).get_urls()

application = MyRESTApiApplication()
