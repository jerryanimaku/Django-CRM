from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils.timezone import now, timedelta
from django.http import HttpResponse
import csv
from .forms import SignUpForm, AddRecordForm, AddTicketForm
from .models import Record, Ticket
import datetime


# Create your views here.
def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Been Logged In!")
            return redirect('home')
        else:
            messages.error(request, "Login failed. Please try again.")
            return redirect('home')
    else:
        records = Record.objects.all()
        paginator = Paginator(records, 10)  # 10 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'home.html', {'records': page_obj})


def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('home')

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Authenticate and Login
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            if user is not None:  # Ensure the user was authenticated successfully
                login(request, user)
                messages.success(request, 'You have successfully registered! Welcome!')
                return redirect('home')
            else:
                messages.error(request, 'Authentication failed. Please try logging in manually.')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def customer_record(request, pk):
	if request.user.is_authenticated:
		# Look Up Records
		customer_record = Record.objects.get(id=pk)
		return render(request, 'record.html', {'customer_record':customer_record})
	else:
		messages.success(request, "You Must Be Logged In To View That Page...")
		return redirect('home')



def delete_record(request, pk):
	if request.user.is_authenticated:
		delete_it = Record.objects.get(id=pk)
		delete_it.delete()
		messages.success(request, "Record Deleted Successfully...")
		return redirect('home')
	else:
		messages.success(request, "You Must Be Logged In To Do That...")
		return redirect('home')


def add_record(request):
	form = AddRecordForm(request.POST or None)
	if request.user.is_authenticated:
		if request.method == "POST":
			if form.is_valid():
				add_record = form.save()
				messages.success(request, "Record Added...")
				return redirect('home')
		return render(request, 'add_record.html', {'form':form})
	else:
		messages.success(request, "You Must Be Logged In...")
		return redirect('home')


def update_record(request, pk):
	if request.user.is_authenticated:
		current_record = Record.objects.get(id=pk)
		form = AddRecordForm(request.POST or None, instance=current_record)
		if form.is_valid():
			form.save()
			messages.success(request, "Record Has Been Updated!")
			return redirect('home')
		return render(request, 'update_record.html', {'form':form})
	else:
		messages.success(request, "You Must Be Logged In...")
		return redirect('home')

def reports(request):
    if request.user.is_authenticated:
        total_records = Record.objects.count()
        customers_by_state = Record.objects.values('state').annotate(count=Count('state')).order_by('-count')
        last_7_days = now() - timedelta(days=7)
        recent_records = Record.objects.filter(created_at__gte=last_7_days)

        paginator = Paginator(recent_records, 5)  # Paginate recent records
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'total_records': total_records,
            'customers_by_state': customers_by_state,
            'recent_records': page_obj,
        }
        return render(request, 'reports.html', context)
    else:
        messages.error(request, "You must be logged in to view reports.")
        return redirect('home')

def export_csv(request):
    if request.user.is_authenticated:
        # Generate CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=customer_records_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv'

        writer = csv.writer(response)
        writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Address', 'City', 'State', 'Zipcode', 'Created At'])
        
        records = Record.objects.all().values_list(
            'first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode', 'created_at'
        )
        for record in records:
            writer.writerow(record)

        return response
    else:
        messages.error(request, "You must be logged in to export reports.")
        return redirect('home')
    

def tickets(request):
    if request.user.is_authenticated:
        tickets = Ticket.objects.all()
        paginator = Paginator(tickets, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.method == 'POST':
            form = AddTicketForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Ticket submitted successfully!")
                return redirect('tickets')
        else:
            form = AddTicketForm()

        return render(request, 'tickets.html', {'tickets': page_obj, 'form': form})
    else:
        messages.error(request, "You must be logged in to manage tickets.")
        return redirect('home')
