from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render


@login_required
def empty(request: HttpRequest) -> HttpResponse:
    context = {}

    return render(request, "ldap/empty.html", context)
