from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date


class Company(models.Model):
    """取引先会社モデル"""
    code = models.CharField(max_length=20, unique=True, verbose_name="会社コード", blank=True)
    name = models.CharField(max_length=255, verbose_name="会社名")
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name="インボイス番号")
    address = models.TextField(blank=True, verbose_name="住所")
    phone = models.CharField(max_length=20, blank=True, verbose_name="電話番号")
    email = models.EmailField(blank=True, verbose_name="メールアドレス")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="担当者名")
    remarks = models.TextField(blank=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "取引先会社"
        verbose_name_plural = "取引先会社"

    def save(self, *args, **kwargs):
        if not self.code:
            # 最大のコード番号を取得して+1
            last_company = Company.objects.order_by('-id').first()
            if last_company and last_company.id:
                next_number = last_company.id + 1
            else:
                next_number = 1
            self.code = f"C{next_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserProfile(models.Model):
    """ユーザープロファイル（Djangoの標準Userモデルを拡張）"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    user_code = models.CharField(max_length=50, unique=True, verbose_name='ユーザーコード', blank=True)
    department = models.CharField(max_length=100, blank=True, verbose_name='部署')
    phone = models.CharField(max_length=20, blank=True, verbose_name='電話番号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    def save(self, *args, **kwargs):
        if not self.user_code:
            # 最新のユーザーコードを取得
            last_profile = UserProfile.objects.order_by('-id').first()
            if last_profile and last_profile.user_code:
                # U0001 から番号を抽出
                try:
                    last_number = int(last_profile.user_code[1:])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            self.user_code = f"U{next_number:04d}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'ユーザープロファイル'
        verbose_name_plural = 'ユーザープロファイル'

    def __str__(self):
        return f"{self.user_code} - {self.user.get_full_name() or self.user.username}"


class Invoice(models.Model):
    """受領請求書モデル"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', '未払い'),
        ('paid', '支払済み'),
        ('overdue', '延滞'),
    ]
    
    auto_number = models.CharField(max_length=50, unique=True, verbose_name="自動連番", blank=True)
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name="請求書番号")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="取引先会社")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="請求金額")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="消費税額")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="合計金額", blank=True)
    invoice_date = models.DateField(verbose_name="請求日")
    due_date = models.DateField(verbose_name="支払期限")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="支払状況")
    description = models.TextField(blank=True, verbose_name="摘要")
    registered_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="登録者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "請求書"
        verbose_name_plural = "請求書"

    def save(self, *args, **kwargs):
        # total_amountを計算
        if self.amount is not None and self.tax_amount is not None:
            self.total_amount = self.amount + self.tax_amount
        
        # auto_numberを自動生成
        if not self.auto_number:
            current_year = date.today().year
            # 同一年の最新の請求書番号を取得
            last_invoice = Invoice.objects.filter(
                auto_number__startswith=f"INV{current_year}"
            ).order_by('-auto_number').first()
            
            if last_invoice and last_invoice.auto_number:
                try:
                    # INV2025-0001 から番号部分を抽出
                    last_number = int(last_invoice.auto_number.split('-')[1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            self.auto_number = f"INV{current_year}-{next_number:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.auto_number} - {self.company.name}"
