from django.shortcuts import redirect

class SmartAdminLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            # avoid redirecting login page to itself 
            if request.path.startswith("/admin") and not request.path.startswith("/admin-login"):
                return redirect("/admin-login/?next=" + request.path)
        return self.get_response(request)
