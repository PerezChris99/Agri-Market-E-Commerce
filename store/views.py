from django.shortcuts import render
from django.http import HttpRequest,HttpResponse

# Create your views here.

def index(request:HttpRequest):
    return HttpResponse("Hello world")

    
