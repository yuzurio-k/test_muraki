from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from invoice_management.models import Company, UserProfile, Invoice


class Command(BaseCommand):
    help = 'サンプルデータを作成します'

    def handle(self, *args, **options):
        self.stdout.write('サンプルデータを作成しています...')

        # 取引先会社を作成
        companies_data = [
            {
                'name': '株式会社サンプル商事',
                'invoice_number': 'T1234567890123',
                'address': '東京都渋谷区渋谷1-1-1',
                'phone': '03-1234-5678',
                'email': 'contact@sample-corp.co.jp',
                'contact_person': '田中太郎'
            },
            {
                'name': 'テスト株式会社',
                'invoice_number': 'T2345678901234',
                'address': '大阪府大阪市北区梅田2-2-2',
                'phone': '06-9876-5432',
                'email': 'info@test-company.co.jp',
                'contact_person': '佐藤花子'
            },
            {
                'name': '例示コーポレーション',
                'invoice_number': '',
                'address': '神奈川県横浜市西区みなとみらい3-3-3',
                'phone': '045-1111-2222',
                'email': 'sales@example-corp.com',
                'contact_person': '鈴木次郎'
            }
        ]

        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults=company_data
            )
            if created:
                self.stdout.write(f'取引先会社を作成しました: {company.name} ({company.code})')

        # テストユーザーを作成
        if not User.objects.filter(username='testuser').exists():
            user = User.objects.create_user(
                username='testuser',
                password='testpass123',
                first_name='山田',
                last_name='太郎',
                email='yamada@example.com'
            )
            UserProfile.objects.create(
                user=user,
                department='経理部',
                phone='03-1234-5678'
            )
            self.stdout.write('テストユーザーを作成しました: testuser')

        # 管理者ユーザーを取得（請求書の登録者として使用）
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('管理者ユーザーが見つかりません'))
            return

        # サンプル請求書を作成
        companies = Company.objects.all()
        invoice_data = [
            {
                'invoice_number': 'BILL-2025-001',
                'company': companies[0],
                'amount': Decimal('100000'),
                'tax_amount': Decimal('10000'),
                'invoice_date': date.today() - timedelta(days=10),
                'due_date': date.today() + timedelta(days=20),
                'payment_status': 'pending',
                'description': '商品販売代金'
            },
            {
                'invoice_number': '',  # 空白でテスト
                'company': companies[1] if len(companies) > 1 else companies[0],
                'amount': Decimal('250000'),
                'tax_amount': Decimal('25000'),
                'invoice_date': date.today() - timedelta(days=5),
                'due_date': date.today() + timedelta(days=25),
                'payment_status': 'paid',
                'description': 'システム開発費用'
            },
            {
                'invoice_number': 'BILL-2025-002',
                'company': companies[2] if len(companies) > 2 else companies[0],
                'amount': Decimal('75000'),
                'tax_amount': Decimal('7500'),
                'invoice_date': date.today() - timedelta(days=15),
                'due_date': date.today() - timedelta(days=5),
                'payment_status': 'pending',
                'description': 'コンサルティング料'
            }
        ]

        for invoice_info in invoice_data:
            # auto_numberが重複しないように確認
            existing_invoice = Invoice.objects.filter(
                company=invoice_info['company'],
                amount=invoice_info['amount']
            ).first()
            
            if not existing_invoice:
                invoice = Invoice.objects.create(
                    **invoice_info,
                    registered_by=admin_user
                )
                self.stdout.write(f'請求書を作成しました: {invoice.auto_number} ({invoice.invoice_number or "番号なし"})')

        self.stdout.write(
            self.style.SUCCESS('サンプルデータの作成が完了しました！')
        )
