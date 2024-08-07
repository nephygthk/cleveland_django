from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import (ListView, TemplateView, CreateView)
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from decimal import Decimal


from .models import (Address, Apointment, Billing, BillingItem, BillingSpecification,
            Customer, Doctor, Patient, Payment, Prescription)
from .forms import (AddDoctorForm, AddressForm, BillSpecificationForm,
            BillingForm, BillingItemFormSet, CustomerUpdateForm, EditBillingItemFormSet, PaymentForm, PrescriptionForm, RegistrationForm, PatientForm, EditPatientForm, UploadImageForm)

def login_user(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('account:admin_dashboard')
        else:
            return redirect('account:patient_status')
        
    try:
        address = Address.objects.get(is_default=True)
    except Address.DoesNotExist:
        address = None

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect('account:admin_dashboard')
            else:
                login(request, user)
                return redirect('account:patient_status')
            
        else:
            messages.info(request, 'Username or password is incorrect')
            return redirect('account:login')
    return render(request, 'account/login.html', {'address':address})


@login_required
def logout_user(request):
    logout(request)
    return redirect('account:login')


class AddPatientView(LoginRequiredMixin, TemplateView):
    model = Customer
    form_class = RegistrationForm
    template_name = 'account2/admin/add_patient.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        registration_form = RegistrationForm(self.request.POST)
        patient_form = PatientForm(self.request.POST, self.request.FILES)
        if registration_form.is_valid() and patient_form.is_valid():
            user = registration_form.save(commit=False)
            user.set_password(registration_form.cleaned_data["password"])
            user.save()
            patient = patient_form.save(commit=False)
            patient.customer = user
            patient.pass_text = registration_form.cleaned_data["password"]
            patient.save()
            
            messages.success(
                self.request,
                    f'Patient created successfully '
                    )

            return HttpResponseRedirect(
                reverse_lazy('account:admin_dashboard')
            )
        
        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                patient_form=patient_form
            )
        )
    
    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = RegistrationForm()
        if 'patient_form' not in kwargs:
            kwargs['patient_form'] = PatientForm()
        return super().get_context_data(**kwargs)
    

class AllPatientView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'account/admin/patient.html'
    context_object_name = 'patients'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)


@login_required
def UpdatePatientView(request, pk):
    if not request.user.is_staff:
        return HttpResponse("Error handler content", status=400)
    customer = get_object_or_404(Customer, pk=pk)
    patient = get_object_or_404(Patient, customer=customer)
    customer_form = CustomerUpdateForm(request.POST or None, instance=customer)
    patient_form = EditPatientForm(request.POST or None, request.FILES or None, instance=patient)

    if all([customer_form.is_valid(), patient_form.is_valid() ]):
        customer_form.save()
        patient_form.save()
        return redirect('account:admin_dashboard')

    context = {'form':customer_form, 'patient_form':patient_form }
    return render(request, "account2/admin/edit_patient.html", context )


@login_required
def delete_patient_account(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    customer.delete()
    messages.success(request, 'Patient deleted successfully')
    return redirect('account:admin_dashboard')


@login_required
def change_patient_password(request, pk):
    customer = Customer.objects.get(pk=pk)
    patient = Patient.objects.get(customer=customer)
    if request.method == 'POST':
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'The password and the repeat password does not match, please try again')
            return redirect('account:change_patient_password', pk=pk)
        else:
            patient.pass_text = password1
            patient.save()
            customer.set_password(password1)
            customer.save()   
        return redirect('account:admin_dashboard')
    context = {'patient':patient}
    return render(request, 'account2/admin/change_customer_passward.html',context)


class AdminDashboardView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'account2/admin/dashboard.html'
    context_object_name = 'customers'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)	
    
    def get_queryset(self):
        # Get the base queryset
        queryset = super().get_queryset().filter(is_staff=False)
        return queryset
    

class AddAndViewDoctorView(LoginRequiredMixin, CreateView):
    form_class = AddDoctorForm
    success_url = reverse_lazy('account:add_doctor')
    template_name = 'account2/admin/list_doctors.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        doc_name = form.cleaned_data.get('doc_name')
        messages.success(
            self.request,
            f'Dr {doc_name} was added successfully'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
       context = super(AddAndViewDoctorView, self).get_context_data(**kwargs)
       context['doctors'] = Doctor.objects.all()
       return context
    

@login_required
def delete_doctor(request, pk):
    doctor = get_object_or_404(Doctor, id=pk)
    doctor.delete()
    messages.success(request, 'Doctor deleted successfully')
    return redirect('account:add_doctor')


@login_required   
def add_new_billing(request):
    if request.method == "POST":
        form = BillingForm(request.POST)
        formset = BillingItemFormSet(request.POST)
        try:
            if form.is_valid and formset.is_valid():
                prices = []
                parent = form.save()
                for form in formset:
                    child = form.save(commit=False)
                    child.billing = parent
                    child.save()
                    prices.append(int(child.bill_value) * (int(child.bill_qty)))
                # price = sum(Decimal(price)  for price in prices)
                # print(type(price))
                parent.bill_amount = sum(Decimal(price)  for price in prices)
                parent.save()
                messages.success(request, 'Bill is created successfully')
                return redirect('account:all_billings')
        except ValueError:
            messages.success(request, 'A bill for this patient already exist')
            return redirect('account:add_billing')
    else:
        form = BillingForm()
        formset = BillingItemFormSet()
    context = {'billing_form':form, 'bill_item_form':formset }
    return render(request, 'account2/admin/add_billing.html', context )


@login_required
def edit_billing(request, pk):
    billing = get_object_or_404(Billing, pk=pk)
    billing_item = BillingItem.objects.filter(billing=billing)
    form = BillingForm(request.POST or None, instance=billing)
    formset = EditBillingItemFormSet(request.POST or None, queryset=billing_item)

    if all([form.is_valid(), formset.is_valid()]):
        prices = []
        parent = form.save()
        # child = formset.save()
        for form in formset:
            child = form.save(commit=False)
            child.billing = parent
            child.save()
            prices.append(int(child.bill_value) * (int(child.bill_qty)))
        parent.bill_amount = sum(Decimal(price)  for price in prices)
        parent.save()

        messages.success(request, 'The bill was updated successfully')
        return redirect('account:all_billings')

    context = {'billing_form':form, 'bill_item_form':formset}
    return render(request, "account2/admin/edit_billing.html", context)


@login_required
def BillingDetailsView(request, pk):
    billing_detail =  get_object_or_404(Billing, pk=pk)
    bill_items = BillingItem.objects.filter(billing=billing_detail)

    context = {'bill':billing_detail, 'bill_items':bill_items}
    return render(request, "account2/admin/list_billing_detail.html", context)


class AllBillingsView(LoginRequiredMixin, ListView):
    model = Billing
    template_name = 'account2/admin/list_billings.html'
    context_object_name = 'billings'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)	
    

@login_required
def delete_billing(request, pk):
    billing = get_object_or_404(Billing, id=pk)
    billing.delete()
    messages.success(request, 'Billing deleted successfully')
    return redirect('account:all_billings')
    
class AddBillSpecificationView(LoginRequiredMixin, CreateView):
    model = BillingSpecification
    form_class = BillSpecificationForm
    template_name = "account2/admin/list_bill_spec.html"
    success_url = reverse_lazy('account:add_billing_specification')

    def get_context_data(self, **kwargs):
       context = super(AddBillSpecificationView, self).get_context_data(**kwargs)
       context['bill_specs'] = BillingSpecification.objects.all()
       return context
    

@login_required
def delete_billing_specification(request, pk):
    billing_spec = get_object_or_404(BillingSpecification, id=pk)
    billing_spec.delete()
    messages.success(request, 'Billing Specification deleted successfully')
    return redirect('account:add_billing_specification')


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'account2/admin/list_payments.html'
    context_object_name = 'payments'
    # paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)	
    

@login_required
def delete_payment(request, pk):
    payment = get_object_or_404(Payment, id=pk)
    payment.delete()
    messages.success(request, 'payment deleted successfully')
    return redirect('account:payment_list')


class PrescriptionView(LoginRequiredMixin, CreateView):
    form_class = PrescriptionForm
    success_url = reverse_lazy('account:add_prescription')
    template_name = 'account2/admin/list_prescriptions.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponse("Error handler content", status=400)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Precsription added successfully'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
       context = super(PrescriptionView, self).get_context_data(**kwargs)
       context['prescriptions'] = Prescription.objects.all()
       return context
    

@login_required
def upload_image_cloudnary(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = UploadImageForm(request.POST or None, request.FILES or None, instance=patient)
    if form.is_valid():
        form.save()
        messages.success(request, 'Image uploaded successfully')
        return redirect('account:all_patient')

    context = {'form':form}
    return render(request, 'account/admin/upload_image_cloudnary.html', context)


from .utils import compress, drastic_compress, small_compress

@login_required
def upload_image(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        image = request.FILES.get('image')
        # print(image.size)
        if image.size > 300000:
            # print("it's greater than 300")
            try:
                final_image = drastic_compress(image)
            except OSError:
                pass

        elif image.size > 169000 and image.size < 300000:
            # print("it's greater than 169")
            try:
                final_image = compress(image)
            except OSError:
                pass
            
        else:
            try:
                final_image = small_compress(image)
            except OSError:
                pass
        patient.picture = final_image
        patient.save()

        response = JsonResponse({"data": "success"})
        return response
        
    context = {'patient':patient}
    return render(request, 'account/admin/upload_image2.html', context)


def add_and_view_addresses(request):
    addresses = Address.objects.all()
    address_form = AddressForm(request.POST or None)

    if address_form.is_valid():
        address_form.save()
        messages.info(request, 'The new address was added successfully')
        return redirect('account:address')

    context = {'form':address_form, 'addresses':addresses}
    return render(request, 'account2/admin/list_addresses.html', context)


def default_address(request, pk):
    Address.objects.filter(is_default=True).update(is_default=False)
    Address.objects.filter(pk=pk).update(is_default=True)
    return redirect('account:address')


def delete_address(request, pk):
    address = Address.objects.get(id=pk)
    if address.is_default == True:
        messages.error(request, "This address can't be deleted because it is currently selected. deselect to delete")
    else:
        address.delete()
        messages.success(request, 'Address deleted successfully')
    return redirect('account:address')

# @login_required
# def upload_image(request, pk):
#     patient = get_object_or_404(Patient, pk=pk)
#     form = UploadImageForm(instance=patient)
#     if request.method == "POST":
#         form = UploadImageForm(request.POST, request.FILES, instance=patient)
#         if form.is_valid():
#             image = form.save(commit=False)
#             image.picture = compress(image.picture)
#             image.save()
#             messages.success(request, "image uploaded successfully")
#             return redirect("account:all_patient")
#     context = {'form':form, 'patient':patient}
#     return render(request, 'account/admin/upload_image2.html', context)







# Patient side
@login_required
def patient_dashboard(request):
    apointments = Apointment.objects.filter(patient=request.user.patient)
    a_length = len(apointments)
    

    context = {'apointments':apointments, 'a_length':a_length}
    return render(request, 'account2/patient/p_dashboard.html', context)


@login_required
def patient_status(request):
    patient = Patient.objects.get(customer=request.user)

    context = {'patient':patient}
    return render(request, 'account2/patient/patient_status.html', context)


@login_required
def patient_billing(request):
    try:
        bills = Billing.objects.filter(patient=request.user.patient)
        bill_items = BillingItem.objects.filter(billing=request.user.patient.billing)

        context = {'bills':bills, 'bill_items': bill_items}
        return render(request, 'account2/patient/patient_billing.html', context)
    except:
        return render(request, 'account2/patient/patient_billing.html')

  
@login_required
def make_payment(request):
    payments = Payment.objects.filter(patient=request.user.patient)
    p_length = len(payments)

    form = PaymentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        try:
            billing = Billing.objects.get(patient=request.user.patient)
            payment = form.save(commit=False)
            payment.patient = request.user.patient
            payment.billing = billing
            payment.save()
            messages.success(request, "Payment receipt uploaded successfully, awaiting verification. Thank you!")
            return redirect('patient:payment')
        
        except Billing.DoesNotExist:
            messages.error(request, "A bill has not been issued to this customer. please contact us for more information")
        
    context = {'payments':payments,'p_length':p_length, 'form':form}
    return render(request, 'account2/patient/payment.html', context)
    # return render(request, 'account/patient/make_payment1.html', context)


# @login_required
# def make_payment(request):
#     payments = Payment.objects.filter(patient=request.user.patient)
#     p_length = len(payments)

#     if request.method == "POST":
#         try:
#             billing = Billing.objects.get(patient=request.user.patient)
#             image = request.FILES.get('image')
#             amount = Decimal(request.POST.get('amount'))
#             summary = request.POST.get('summary')

#             Payment.objects.create(billing=billing, patient=request.user.patient,
#                                 amount=amount, receipt=image, payment_summary=summary)
#             response = JsonResponse({"data": "success"})
#             return response
#         except Billing.DoesNotExist:
#             messages.error(request, "A bill has not been issued to this customer. please contact us for more information")
#             return redirect('account:make_payment')
        

#     context = {'payments':payments,'p_length':p_length}
#     return render(request, 'account2/patient/payment.html', context)


def view_receipt(request, pk):
    billing = get_object_or_404(Billing, pk=pk)
    bill_items = BillingItem.objects.filter(billing=billing)
    address = Address.objects.get(is_default=True)

    context = {'billing':billing, 'bill_items':bill_items, 'address':address}
    return render(request, 'account2/receipt/bill_receipt3.html', context)



from django.core.mail import send_mail

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
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
            return redirect('account:contact')  
    return render(request, 'account2/patient/contact.html')




# @login_required
# def make_payment(request):
#     payments = Payment.objects.filter(patient=request.user.patient)
#     p_length = len(payments)
#     payment_form = PaymentForm()

#     if request.method == "POST":
#         try:
#             billing = Billing.objects.get(patient=request.user.patient)
#             payment_form = PaymentForm(request.POST, request.FILES)
#             if payment_form.is_valid():
#                 payment = payment_form.save(commit=False)
#                 payment.patient = request.user.patient
#                 payment.billing = billing
#                 payment.save()
#                 messages.success(request, "Payment receipt uploaded successfully, awaiting verification. Thank you!")
#                 return redirect('account:make_payment')
#         except Billing.DoesNotExist:
#             messages.error(request, "A bill has not been issued to this customer. please contact us for more information")

#     context = {'payments':payments, 'form': payment_form, 'p_length':p_length}
#     return render(request, 'account/patient/make_payment1.html', context)