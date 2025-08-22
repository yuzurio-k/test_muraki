from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Company, UserProfile, Invoice


class CompanyForm(forms.ModelForm):
    """取引先会社登録フォーム"""
    class Meta:
        model = Company
        fields = ['name', 'invoice_number', 'address', 'phone', 'email', 'contact_person', 'remarks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社名を入力'}),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '13桁の数字を入力（任意）',
                'maxlength': '13',
                'pattern': '[0-9]{13}',
                'id': 'invoice_number_input'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '住所を入力'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '電話番号を入力'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '担当者名を入力'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '備考を入力（任意）'}),
        }
    
    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number')
        if invoice_number:
            # Tが既についている場合は除去
            if invoice_number.startswith('T'):
                invoice_number = invoice_number[1:]
            
            # 数字以外が含まれていないかチェック
            if not invoice_number.isdigit():
                raise forms.ValidationError('インボイス番号は数字のみで入力してください。')
            
            # 13桁かチェック
            if len(invoice_number) != 13:
                raise forms.ValidationError('インボイス番号は13桁の数字で入力してください。')
            
            # T接頭辞を追加
            return f'T{invoice_number}'
        
        return invoice_number


class UserRegistrationForm(UserCreationForm):
    """ユーザー登録フォーム"""
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '名前を入力'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '苗字を入力'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'})
    )
    is_staff = forms.BooleanField(
        required=False,
        label='管理者権限',
        help_text='チェックすると管理者として登録されます',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '部署を入力'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '電話番号を入力'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名を入力'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'パスワードを入力'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'パスワードを再入力'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.is_staff = self.cleaned_data['is_staff']  # 管理者権限を設定
        
        if commit:
            user.save()
            # UserProfileを作成（user_codeは自動生成）
            UserProfile.objects.create(
                user=user,
                department=self.cleaned_data['department'],
                phone=self.cleaned_data['phone']
            )
        return user


class UserEditForm(forms.ModelForm):
    """ユーザー編集フォーム（パスワード変更なし）"""
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '名前を入力'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '苗字を入力'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'})
    )
    is_staff = forms.BooleanField(
        required=False,
        label='管理者権限',
        help_text='チェックすると管理者として設定されます',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名を入力'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class InvoiceForm(forms.ModelForm):
    """請求書登録フォーム"""
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'company', 'amount', 'tax_amount', 
            'invoice_date', 'due_date', 'payment_status', 'description'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '請求書番号を入力（任意）'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control',
                'id': 'company-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '請求金額を入力',
                'min': '0'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '消費税額を入力',
                'min': '0'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': '摘要を入力'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 会社をコード順（新しい順）で表示し、選択肢をより見やすくする
        self.fields['company'].queryset = Company.objects.all().order_by('-code')
        self.fields['company'].empty_label = "取引先会社を選択してください"

    def clean_company(self):
        """companyフィールドのカスタムバリデーション"""
        company = self.cleaned_data.get('company')
        if not company:
            raise forms.ValidationError('取引先会社を選択してください。')
        return company
