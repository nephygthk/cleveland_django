from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.contrib import messages

from account.models import Address



class Home(TemplateView):
    template_name = 'frontend/index.html'
  
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('account:admin_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('account:patient_status'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        try:
            context['address'] = Address.objects.get(is_default=True)
        except Address.DoesNotExist:
            pass
        return context
    


class Contact(TemplateView):
    template_name = 'frontend/contact.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('account:admin_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('account:patient_status'))
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        try:
            send_mail(
                'Message From '+name+' <'+email+'>',
                message,
                'contact@clevelandmedcenter.org',
                ['contact@clevelandmedcenter.org'],
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully, we will get back to you as soon as possible')
        except:
            messages.error(request, 'There was an error while trying to send your email, please try again')

        finally:
            return HttpResponseRedirect(reverse_lazy('frontend:contact'))
        
    def get_context_data(self, **kwargs):
        context = super(Contact, self).get_context_data(**kwargs)
        context['address'] = Address.objects.get(is_default=True)
        return context
