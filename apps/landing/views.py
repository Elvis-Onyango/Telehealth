from django.shortcuts import render

# Create your views here.

def landing_page(requests):
	return render(requests, 'landing/index.html')
