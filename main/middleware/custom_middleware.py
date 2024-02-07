# custom_middleware.py

from django.shortcuts import redirect
from django.urls import reverse

class RedirectUnauthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URL patterns that should not trigger the redirect
        exclude_paths = [reverse('login_user'), reverse('sign_up'), reverse('password_reset'), reverse('home')] 

        # Check if the user is not authenticated and the requested URL is not excluded
        if not request.user.is_authenticated and request.path not in exclude_paths:
            # Store the requested URL in the session
            request.session['next'] = request.get_full_path()
            # Redirect to the login page
            return redirect(reverse('login_user'))
        if request.user.is_authenticated and request.path == reverse('login_user'):
            # Redirect to a different page
            return redirect(reverse('home'))
        if request.user.is_authenticated and request.path == reverse('login'):
            # Redirect to a different page
            return redirect(reverse('home'))
        response = self.get_response(request)
        return response

class Redirect404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return redirect(reverse('home'))
        return response