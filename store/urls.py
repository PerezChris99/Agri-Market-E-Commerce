from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.store, name="store"),
    path('cart/',views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),

    path('update_item/', views.updateItem, name="update_item"),

    # add to cart path
    path('add-to-cart/<int:item_id>', views.add_to_cart, name="add_to_cart"),

    path('process_order/', views.processOrder, name="process_order"),

    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logout_user,name="logout"),
]