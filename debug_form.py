from invoice_management.forms import InvoiceForm

form = InvoiceForm()
print("Company field:")
print(form['company'])
print(f"Company field ID: {form['company'].id_for_label}")
print(f"Hidden field: {form['company'].as_hidden()}")
