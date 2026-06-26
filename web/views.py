from django.shortcuts import render
from django.template.response import TemplateResponse

# Create your views here.
def lokfuehrer_index(request):

    return TemplateResponse(request, "lokfuehrer.html", {})



