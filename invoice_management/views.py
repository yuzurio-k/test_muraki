from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.contrib.auth import login
from datetime import datetime, date
import calendar
from .models import Company, UserProfile, Invoice
from .forms import CompanyForm, UserRegistrationForm, UserEditForm, InvoiceForm


def dashboard(request):
    """ダッシュボード"""
    if request.user.is_authenticated:
        # 統計情報を取得
        total_invoices = Invoice.objects.count()
        pending_invoices = Invoice.objects.filter(payment_status='pending').count()
        total_amount = Invoice.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        pending_amount = Invoice.objects.filter(
            payment_status='pending'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # 最近の請求書
        recent_invoices = Invoice.objects.select_related('company').order_by('-created_at')[:5]
        
        context = {
            'total_invoices': total_invoices,
            'pending_invoices': pending_invoices,
            'total_amount': total_amount,
            'pending_amount': pending_amount,
            'recent_invoices': recent_invoices,
        }
    else:
        context = {}
    
    return render(request, 'invoice_management/dashboard.html', context)


@login_required
def company_list(request):
    """取引先会社一覧"""
    companies = Company.objects.all().order_by('-code')
    
    # 検索機能
    search_query = request.GET.get('search')
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) | 
            Q(code__icontains=search_query)
        )
    
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'invoice_management/company_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


@login_required
def company_add(request):
    """取引先会社追加"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '取引先会社を登録しました。')
            return redirect('company_list')
    else:
        form = CompanyForm()
    
    return render(request, 'invoice_management/company_form.html', {
        'form': form,
        'title': '取引先会社登録'
    })


@login_required
def company_edit(request, pk):
    """取引先会社編集"""
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, '取引先会社を更新しました。')
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'invoice_management/company_form.html', {
        'form': form,
        'title': '取引先会社編集',
        'company': company
    })


@login_required
def user_list(request):
    """ユーザー一覧"""
    # 管理者またはスーパーユーザーのみアクセス可能
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'この機能にアクセスする権限がありません。')
        return redirect('dashboard')
    
    # スーパーユーザーを除外してユーザーを取得
    users = User.objects.select_related('userprofile').filter(is_superuser=False).order_by('username')
    
    # 検索機能
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(userprofile__user_code__icontains=search_query)
        )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'invoice_management/user_list.html', {
        'page_obj': page_obj,
        'users': users,  # テンプレートで使用するため追加
        'search_query': search_query
    })


@login_required
def user_add(request):
    """ユーザー追加（管理者・スーパーユーザーのみ）"""
    # 管理者またはスーパーユーザーのみアクセス可能
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'この機能にアクセスする権限がありません。')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ユーザーを追加しました。')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'invoice_management/user_form.html', {
        'form': form,
        'title': 'ユーザー追加'
    })


@login_required
def user_edit(request, pk):
    """ユーザー編集"""
    user = get_object_or_404(User, pk=pk)
    
    # 権限チェック
    # - スーパーユーザー: 全員編集可能
    # - 管理者: 自分以外の一般ユーザー編集可能（スーパーユーザーは除く）
    # - 一般ユーザー: 自分のみ編集可能
    if not request.user.is_superuser:
        if request.user.is_staff:
            # 管理者は自分以外の一般ユーザーのみ編集可能
            if user.is_superuser or (user.is_staff and user != request.user):
                messages.error(request, 'このユーザーを編集する権限がありません。')
                return redirect('user_list')
        else:
            # 一般ユーザーは自分のみ編集可能
            if user != request.user:
                messages.error(request, '自分以外のユーザーを編集する権限がありません。')
                return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        
        # 権限に応じてフォームを制限
        if not request.user.is_superuser and not request.user.is_staff:
            # 一般ユーザーは管理者権限を変更できない
            form.fields.pop('is_staff', None)
        elif not request.user.is_superuser and request.user.is_staff and user == request.user:
            # 管理者も自分の管理者権限は変更できない
            form.fields.pop('is_staff', None)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'ユーザー「{user.username}」を更新しました。')
            if request.user.is_staff or request.user.is_superuser:
                return redirect('user_list')
            else:
                return redirect('dashboard')
    else:
        form = UserEditForm(instance=user)
        
        # 権限に応じてフォームを制限
        if not request.user.is_superuser and not request.user.is_staff:
            # 一般ユーザーは管理者権限を変更できない
            form.fields.pop('is_staff', None)
        elif not request.user.is_superuser and request.user.is_staff and user == request.user:
            # 管理者も自分の管理者権限は変更できない
            form.fields.pop('is_staff', None)
    
    return render(request, 'invoice_management/user_form.html', {
        'form': form,
        'title': f'ユーザー編集 - {user.username}'
    })


@login_required
def user_delete(request, pk):
    """ユーザー削除"""
    user = get_object_or_404(User, pk=pk)
    
    # 権限チェック：管理者またはスーパーユーザーのみ
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'ユーザーを削除する権限がありません。')
        return redirect('dashboard')
    
    # 自分自身は削除できない
    if user == request.user:
        messages.error(request, '自分自身を削除することはできません。')
        return redirect('user_list')
    
    # 管理者はスーパーユーザーを削除できない
    if not request.user.is_superuser and user.is_superuser:
        messages.error(request, 'スーパーユーザーを削除する権限がありません。')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'ユーザー「{username}」を削除しました。')
        return redirect('user_list')
    
    return redirect('user_list')


@login_required
def user_password_change(request, pk):
    """ユーザーパスワード変更"""
    user = get_object_or_404(User, pk=pk)
    
    # パスワード変更は自分のもののみ可能（スーパーユーザーは例外）
    if not request.user.is_superuser and user != request.user:
        messages.error(request, '他のユーザーのパスワードを変更する権限がありません。')
        return redirect('user_edit', pk=pk)
    
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 == new_password2:
                if len(new_password1) >= 8:
                    user.set_password(new_password1)
                    user.save()
                    messages.success(request, f'ユーザー「{user.username}」のパスワードを変更しました。')
                else:
                    messages.error(request, 'パスワードは8文字以上で設定してください。')
            else:
                messages.error(request, 'パスワードが一致しません。')
        else:
            messages.error(request, 'パスワードを入力してください。')
    
    return redirect('user_edit', pk=pk)


@login_required
def invoice_list(request):
    """請求書一覧"""
    invoices = Invoice.objects.select_related('company', 'registered_by').order_by('-created_at')
    
    # フィルタリング
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(payment_status=status_filter)
    
    company_filter = request.GET.get('company')
    if company_filter:
        invoices = invoices.filter(company_id=company_filter)
    
    # 金額範囲検索
    amount_min = request.GET.get('amount_min')
    amount_max = request.GET.get('amount_max')
    if amount_min:
        try:
            invoices = invoices.filter(total_amount__gte=amount_min)
        except ValueError:
            pass
    if amount_max:
        try:
            invoices = invoices.filter(total_amount__lte=amount_max)
        except ValueError:
            pass
    
    # 請求日範囲検索
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            invoices = invoices.filter(invoice_date__gte=date_from)
        except ValueError:
            pass
    if date_to:
        try:
            invoices = invoices.filter(invoice_date__lte=date_to)
        except ValueError:
            pass
    
    # 検索機能
    search_query = request.GET.get('search')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(auto_number__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # フィルタ用のデータ
    companies = Company.objects.all().order_by('name')
    status_choices = Invoice.PAYMENT_STATUS_CHOICES
    
    return render(request, 'invoice_management/invoice_list.html', {
        'page_obj': page_obj,
        'companies': companies,
        'status_choices': status_choices,
        'current_status': status_filter,
        'current_company': company_filter,
        'search_query': search_query,
        'amount_min': amount_min,
        'amount_max': amount_max,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def invoice_add(request):
    """請求書追加"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.registered_by = request.user
            invoice.save()
            messages.success(request, '請求書を登録しました。')
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
    
    return render(request, 'invoice_management/invoice_form.html', {
        'form': form,
        'title': '請求書登録'
    })


@login_required
def invoice_edit(request, pk):
    """請求書編集"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, '請求書を更新しました。')
            return redirect('invoice_list')
    else:
        form = InvoiceForm(instance=invoice)
    
    return render(request, 'invoice_management/invoice_form.html', {
        'form': form,
        'title': '請求書編集',
        'invoice': invoice
    })


@login_required
def invoice_detail(request, pk):
    """請求書詳細"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    return render(request, 'invoice_management/invoice_detail.html', {
        'invoice': invoice
    })


@login_required
def monthly_report(request):
    """月別請求金額レポート"""
    # 年の選択（デフォルトは今年）
    current_year = datetime.now().year
    selected_year = int(request.GET.get('year', current_year))
    
    # 税込・税抜の選択（デフォルトは税込）
    tax_mode = request.GET.get('tax_mode', 'including')  # 'including' or 'excluding'
    
    # 取引先会社を取得
    companies = Company.objects.all().order_by('name')
    
    # 選択した年の請求書データを取得
    invoices = Invoice.objects.filter(
        invoice_date__year=selected_year
    ).select_related('company')
    
    # 月別データを整理
    monthly_data = {}
    monthly_totals = {}
    company_totals = {}
    
    # 月別合計を初期化
    for month in range(1, 13):
        monthly_totals[month] = 0
    
    # 各会社の月別データを初期化
    for company in companies:
        monthly_data[company.id] = {
            'company': company,
            'months': {}
        }
        company_totals[company.id] = 0
        for month in range(1, 13):
            monthly_data[company.id]['months'][month] = 0
    
    # 請求書データを月別に集計
    for invoice in invoices:
        company_id = invoice.company.id
        month = invoice.invoice_date.month
        
        # 税込・税抜の選択に応じて金額を設定
        if tax_mode == 'excluding':
            amount = int(invoice.amount)  # 税抜金額
        else:
            amount = int(invoice.total_amount)  # 税込金額（デフォルト）
        
        if company_id in monthly_data:
            monthly_data[company_id]['months'][month] += amount
            monthly_totals[month] += amount
            company_totals[company_id] += amount
    
    # 月名リストを作成
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    
    # 年のリストを作成（過去5年から未来2年）
    year_range = range(current_year - 5, current_year + 3)
    
    # 総合計を計算
    grand_total = sum(company_totals.values())
    
    # 合計金額順にソートしたmonthly_dataを作成
    sorted_monthly_data = dict(sorted(
        monthly_data.items(),
        key=lambda x: company_totals[x[0]],
        reverse=True
    ))
    
    # 最高取引先を計算
    top_company = None
    if company_totals:
        max_amount = max(company_totals.values())
        for company_id, total in company_totals.items():
            if total == max_amount:
                top_company = monthly_data[company_id]['company']
                break
    
    context = {
        'selected_year': selected_year,
        'year_range': year_range,
        'monthly_data': sorted_monthly_data,
        'monthly_totals': monthly_totals,
        'company_totals': company_totals,
        'month_names': month_names,
        'grand_total': grand_total,
        'top_company': top_company,
        'months': range(1, 13),
        'tax_mode': tax_mode,
        'tax_mode_display': '税抜' if tax_mode == 'excluding' else '税込',
    }
    
    return render(request, 'invoice_management/monthly_report.html', context)


@login_required
def analytics_report(request):
    """分析レポート"""
    # 年の選択（デフォルトは今年）
    current_year = datetime.now().year
    selected_year = int(request.GET.get('year', current_year))
    
    # 税込・税抜の選択（デフォルトは税込）
    tax_mode = request.GET.get('tax_mode', 'including')  # 'including' or 'excluding'
    
    # 年間データを取得
    invoices = Invoice.objects.filter(
        invoice_date__year=selected_year
    ).select_related('company')
    
    # 月別合計データ
    monthly_chart_data = []
    monthly_totals = {}
    for month in range(1, 13):
        monthly_totals[month] = 0
    
    for invoice in invoices:
        month = invoice.invoice_date.month
        # 税込・税抜の選択に応じて金額を設定
        if tax_mode == 'excluding':
            amount = int(invoice.amount)  # 税抜金額
        else:
            amount = int(invoice.total_amount)  # 税込金額（デフォルト）
        monthly_totals[month] += amount
    
    # Chart.js用の月別データ
    for month in range(1, 13):
        monthly_chart_data.append({
            'month': f'{month}月',
            'amount': monthly_totals[month]
        })
    
    # 会社別年間合計（トップ10）
    company_yearly_totals = {}
    for invoice in invoices:
        company_id = invoice.company.id
        company_name = invoice.company.name
        # 税込・税抜の選択に応じて金額を設定
        if tax_mode == 'excluding':
            amount = int(invoice.amount)  # 税抜金額
        else:
            amount = int(invoice.total_amount)  # 税込金額（デフォルト）
        
        if company_id not in company_yearly_totals:
            company_yearly_totals[company_id] = {
                'name': company_name,
                'total': 0
            }
        company_yearly_totals[company_id]['total'] += amount
    
    # トップ10会社を取得
    top_companies = sorted(
        company_yearly_totals.values(),
        key=lambda x: x['total'],
        reverse=True
    )[:10]
    
    # 支払状況別統計
    status_stats = {
        'pending': invoices.filter(payment_status='pending').count(),
        'paid': invoices.filter(payment_status='paid').count(),
        'overdue': invoices.filter(payment_status='overdue').count(),
    }
    
    # 会社別円グラフ用データ（トップ10会社）
    company_chart_data = []
    other_total = 0
    for i, company in enumerate(top_companies):
        if i < 10:  # トップ10まで
            company_chart_data.append({
                'name': company['name'],
                'value': company['total']
            })
        else:
            other_total += company['total']
    
    # その他の会社がある場合は追加
    if other_total > 0:
        company_chart_data.append({
            'name': 'その他',
            'value': other_total
        })
    
    # 統計情報
    total_invoices = invoices.count()
    if tax_mode == 'excluding':
        total_amount = sum(int(invoice.amount) for invoice in invoices)
    else:
        total_amount = sum(int(invoice.total_amount) for invoice in invoices)
    avg_amount = total_amount / total_invoices if total_invoices > 0 else 0
    
    # 年のリストを作成
    year_range = range(current_year - 5, current_year + 3)
    
    context = {
        'selected_year': selected_year,
        'year_range': year_range,
        'monthly_chart_data': monthly_chart_data,
        'top_companies': top_companies,
        'company_chart_data': company_chart_data,
        'status_stats': status_stats,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'tax_mode': tax_mode,
        'tax_mode_display': '税抜' if tax_mode == 'excluding' else '税込',
    }
    
    return render(request, 'invoice_management/analytics_report.html', context)


@login_required
def monthly_detail_report(request):
    """月別詳細レポート"""
    # 年月の選択（デフォルトは今月）
    current_date = datetime.now()
    selected_year = int(request.GET.get('year', current_date.year))
    selected_month = int(request.GET.get('month', current_date.month))
    
    # 税込・税抜の選択（デフォルトは税込）
    tax_mode = request.GET.get('tax_mode', 'including')  # 'including' or 'excluding'
    
    # 選択した年月の請求書データを取得
    invoices = Invoice.objects.filter(
        invoice_date__year=selected_year,
        invoice_date__month=selected_month
    ).select_related('company', 'registered_by').order_by('-total_amount')
    
    # 統計情報
    total_invoices = invoices.count()
    if tax_mode == 'excluding':
        total_amount = sum(int(invoice.amount) for invoice in invoices)
    else:
        total_amount = sum(int(invoice.total_amount) for invoice in invoices)
    avg_amount = total_amount / total_invoices if total_invoices > 0 else 0
    
    # 支払状況別統計
    status_stats = {
        'pending': invoices.filter(payment_status='pending').count(),
        'paid': invoices.filter(payment_status='paid').count(),
        'overdue': invoices.filter(payment_status='overdue').count(),
    }
    
    # 会社別集計
    company_totals = {}
    for invoice in invoices:
        company_id = invoice.company.id
        company_name = invoice.company.name
        # 税込・税抜の選択に応じて金額を設定
        if tax_mode == 'excluding':
            amount = int(invoice.amount)  # 税抜金額
        else:
            amount = int(invoice.total_amount)  # 税込金額（デフォルト）
        
        if company_id not in company_totals:
            company_totals[company_id] = {
                'name': company_name,
                'total': 0,
                'count': 0
            }
        company_totals[company_id]['total'] += amount
        company_totals[company_id]['count'] += 1
    
    # 会社別を金額順にソート
    sorted_companies = sorted(
        company_totals.values(),
        key=lambda x: x['total'],
        reverse=True
    )
    
    # 会社別円グラフ用データ（トップ10会社）
    company_chart_data = []
    other_total = 0
    for i, company in enumerate(sorted_companies):
        if i < 10:  # トップ10まで
            company_chart_data.append({
                'name': company['name'],
                'value': company['total']
            })
        else:
            other_total += company['total']
    
    # その他の会社がある場合は追加
    if other_total > 0:
        company_chart_data.append({
            'name': 'その他',
            'value': other_total
        })
    
    # 年月のリストを作成
    year_range = range(current_date.year - 5, current_date.year + 3)
    month_range = range(1, 13)
    
    context = {
        'selected_year': selected_year,
        'selected_month': selected_month,
        'year_range': year_range,
        'month_range': month_range,
        'invoices': invoices,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'status_stats': status_stats,
        'sorted_companies': sorted_companies,
        'company_chart_data': company_chart_data,
        'tax_mode': tax_mode,
        'tax_mode_display': '税抜' if tax_mode == 'excluding' else '税込',
    }
    
    return render(request, 'invoice_management/monthly_detail_report.html', context)


@login_required
def company_detail_report(request):
    """会社別詳細レポート"""
    # 会社の選択
    company_id = request.GET.get('company')
    selected_year = int(request.GET.get('year', datetime.now().year))
    
    # 税込・税抜の選択（デフォルトは税込）
    tax_mode = request.GET.get('tax_mode', 'including')  # 'including' or 'excluding'
    
    companies = Company.objects.all().order_by('-created_at', 'name')
    
    if company_id:
        company = get_object_or_404(Company, pk=company_id)
    else:
        company = None
    
    if company:
        
        # 選択した会社の請求書データを取得
        invoices = Invoice.objects.filter(
            company=company,
            invoice_date__year=selected_year
        ).select_related('registered_by').order_by('-invoice_date')
        
        # 月別データ
        monthly_data = {}
        for month in range(1, 13):
            monthly_data[month] = {
                'total': 0,
                'count': 0,
                'invoices': []
            }
        
        for invoice in invoices:
            month = invoice.invoice_date.month
            # 税込・税抜の選択に応じて金額を設定
            if tax_mode == 'excluding':
                amount = int(invoice.amount)  # 税抜金額
            else:
                amount = int(invoice.total_amount)  # 税込金額（デフォルト）
            monthly_data[month]['total'] += amount
            monthly_data[month]['count'] += 1
            monthly_data[month]['invoices'].append(invoice)
        
        # 統計情報
        total_invoices = invoices.count()
        if tax_mode == 'excluding':
            total_amount = sum(int(invoice.amount) for invoice in invoices)
        else:
            total_amount = sum(int(invoice.total_amount) for invoice in invoices)
        avg_amount = total_amount / total_invoices if total_invoices > 0 else 0
        
        # 支払状況別統計
        status_stats = {
            'pending': invoices.filter(payment_status='pending').count(),
            'paid': invoices.filter(payment_status='paid').count(),
            'overdue': invoices.filter(payment_status='overdue').count(),
        }
        
        # Chart.js用の月別データ
        monthly_chart_data = []
        for month in range(1, 13):
            monthly_chart_data.append({
                'month': f'{month}月',
                'amount': monthly_data[month]['total']
            })
        
        # 月別支払い円グラフ用データ（金額がある月のみ）
        monthly_pie_data = []
        for month in range(1, 13):
            if monthly_data[month]['total'] > 0:
                monthly_pie_data.append({
                    'month': f'{month}月',
                    'amount': monthly_data[month]['total']
                })
    else:
        company = None
        invoices = Invoice.objects.none()
        monthly_data = {}
        total_invoices = 0
        total_amount = 0
        avg_amount = 0
        status_stats = {'pending': 0, 'paid': 0, 'overdue': 0}
        monthly_chart_data = []
        monthly_pie_data = []
    
    # 年のリストを作成
    year_range = range(datetime.now().year - 5, datetime.now().year + 3)
    
    context = {
        'companies': companies,
        'selected_company': company,
        'selected_year': selected_year,
        'year_range': year_range,
        'invoices': invoices,
        'monthly_data': monthly_data,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'status_stats': status_stats,
        'monthly_chart_data': monthly_chart_data,
        'monthly_pie_data': monthly_pie_data,
        'months': range(1, 13),
        'tax_mode': tax_mode,
        'tax_mode_display': '税抜' if tax_mode == 'excluding' else '税込',
    }
    
    return render(request, 'invoice_management/company_detail_report.html', context)
