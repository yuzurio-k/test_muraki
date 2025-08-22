from invoice_management.models import Company

print(f'Total companies: {Company.objects.count()}')
for c in Company.objects.all()[:10]:
    print(f'{c.code} - {c.name}')
