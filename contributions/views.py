import hashlib
from urllib.parse import urlparse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import ContributionForm, LoginForm, SignupForm
from .models import Contribution

def _target(request, model=None):
    url = reverse("detail", args=[model.slug]) if model else reverse("catalog")
    return url + "?lang=" + ("en" if request.GET.get("lang") == "en" else "ru") + "#contributions"

def _valid_url(url):
    parsed = urlparse(url)
    return not url or (parsed.scheme == "https" and bool(parsed.netloc))

def handle_post(request, model=None):
    action = request.POST.get("action")
    if action == "logout":
        logout(request)
        return HttpResponseRedirect(_target(request, model))
    if action == "login":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user:
                login(request, user)
                return HttpResponseRedirect(_target(request, model))
        messages.error(request, "Invalid sign-in.")
        return HttpResponseRedirect(_target(request, model))
    if action == "signup":
        form = SignupForm(request.POST)
        if form.is_valid() and not User.objects.filter(username=form.cleaned_data["username"]).exists():
            user = User.objects.create_user(form.cleaned_data["username"], password=form.cleaned_data["password"])
            login(request, user)
            return HttpResponseRedirect(_target(request, model))
        messages.error(request, "This account cannot be created.")
        return HttpResponseRedirect(_target(request, model))
    if action == "propose":
        if not request.user.is_authenticated:
            messages.error(request, "Sign in before sending a proposal.")
            return HttpResponseRedirect(_target(request, model))
        form = ContributionForm(request.POST)
        if form.is_valid() and _valid_url(form.cleaned_data["source_url"]):
            snapshot = "" if model is None else f"{model.pk}:{model.checked}:{model.name}:{model.version}"
            Contribution.objects.create(kind=form.cleaned_data["kind"], model=model, author=request.user,
                payload={"title": form.cleaned_data["title"], "details": form.cleaned_data["details"]},
                expected_hash=hashlib.sha256(snapshot.encode()).hexdigest() if snapshot else "",
                source_url=form.cleaned_data["source_url"], translation_only=form.cleaned_data["translation_only"])
            messages.success(request, "Proposal sent for editorial review.")
        else:
            messages.error(request, "Check the proposal fields and its HTTPS source.")
        return HttpResponseRedirect(_target(request, model))
    return None

def panel_context(request, model=None):
    return {"contribution_form": ContributionForm(initial={"kind": "edit_model" if model else "new_model"}),
            "login_form": LoginForm(), "signup_form": SignupForm(),
            "contribution_history": Contribution.objects.filter(model=model)[:20] if model else []}
