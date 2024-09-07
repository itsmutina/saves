from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Income, Expense
from django.db.models.functions import TruncMonth
from django.utils import timezone

#@login_required
def dashboard(request):
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)
    
    # Calculate totals
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    net_income = total_income - total_expenses
    savings_rate = (net_income / total_income * 100) if total_income > 0 else 0

    # Get last 10 entries (combined income and expenses)
    last_10_entries = sorted(
        list(incomes.order_by('-date')[:5]) + list(expenses.order_by('-date')[:5]),
        key=lambda x: x.date,
        reverse=True
    )[:10]

    # Prepare data for progress chart (last 6 months)
    six_months_ago = timezone.now().date() - timezone.timedelta(days=180)
    monthly_data = (
        Income.objects.filter(user=request.user, date__gte=six_months_ago)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(income=Sum('amount'))
        .order_by('month')
    )
    monthly_expenses = (
        Expense.objects.filter(user=request.user, date__gte=six_months_ago)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(expenses=Sum('amount'))
        .order_by('month')
    )

    # Combine income and expenses data
    monthly_summary = {}
    for entry in monthly_data:
        monthly_summary[entry['month']] = {'income': entry['income'], 'expenses': 0}
    for entry in monthly_expenses:
        if entry['month'] in monthly_summary:
            monthly_summary[entry['month']]['expenses'] = entry['expenses']
        else:
            monthly_summary[entry['month']] = {'income': 0, 'expenses': entry['expenses']}

    # Convert to list for easy use in template
    monthly_summary = [
        {
            'month': k.strftime('%B %Y'),
            'income': v['income'],
            'expenses': v['expenses'],
            'savings': v['income'] - v['expenses']
        }
        for k, v in monthly_summary.items()
    ]

    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'savings_rate': savings_rate,
        'last_10_entries': last_10_entries,
        'monthly_summary': monthly_summary,
    }
    return render(request, 'tracker/dashboard.html', context)
#@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('dashboard')
    else:
        form = IncomeForm()
    return render(request, 'tracker/add_income.html', {'form': form})

#@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})

#@login_required
def reports(request):
    # Get data for the last 6 months
    six_months_ago = timezone.now().date() - timezone.timedelta(days=180)
    
    incomes = Income.objects.filter(user=request.user, date__gte=six_months_ago)
    expenses = Expense.objects.filter(user=request.user, date__gte=six_months_ago)
    
    # Prepare data for income vs expense chart
    monthly_data = (
        incomes.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(income=Sum('amount'))
        .order_by('month')
    )
    
    monthly_expenses = (
        expenses.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(expense=Sum('amount'))
        .order_by('month')
    )
    
    # Combine income and expense data
    combined_data = {}
    for entry in monthly_data:
        combined_data[entry['month']] = {'income': entry['income'], 'expense': 0}
    for entry in monthly_expenses:
        if entry['month'] in combined_data:
            combined_data[entry['month']]['expense'] = entry['expense']
        else:
            combined_data[entry['month']] = {'income': 0, 'expense': entry['expense']}
    
    # Convert to list for easy use in template
    income_expense_data = [
        {
            'month': k.strftime('%B %Y'),
            'income': v['income'],
            'expense': v['expense']
        }
        for k, v in combined_data.items()
    ]
    
    # Prepare data for expense by category chart
    expense_by_category = (
        expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    context = {
        'income_expense_data': income_expense_data,
        'expense_by_category': list(expense_by_category),
    }
    return render(request, 'tracker/reports.html', context)