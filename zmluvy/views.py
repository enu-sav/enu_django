from django.shortcuts import render
from django.http import HttpResponse
from ipdb import set_trace as trace


def index(request):
    return HttpResponse("Hello, world. You're at the contract index.")

from django.utils import timezone
from django.views.generic.list import ListView

from .models import OsobaAutor

#zodpovedajuce view: zmluvy/templates/zmluvy/osobaautor_list.html
#zobrazuje sa context['object_list']
class OsobaAutorListView(ListView):

    model = OsobaAutor
    paginate_by = 30  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #trace()
        context['now'] = timezone.now()
        return context

