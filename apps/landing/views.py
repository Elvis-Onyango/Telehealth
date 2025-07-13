from django.shortcuts import render

# Create your views here.

def landing_page(requests):
	return render(requests, 'landing/index.html')


def api_testing(requests):
	return render(requests,'landing/test.html')