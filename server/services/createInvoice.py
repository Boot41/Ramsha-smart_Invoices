

from schemas.invoice_schemas import RentalAgreementCreate, RentalAgreementStatus, RentPaymentCreate, PaymentStatus
from google.cloud import firestore
import uuid
from datetime import datetime, date

async def store_invoice_data(create_invoice_data: CreateInvoiceFirestore, email: str, org: str):
    """ Stores invoice data in Firestore under draft_invoice/{customer_id}/{invoice_id} using the new InvoiceDetails schema.

    Args:
        create_invoice_data: An instance of CreateInvoiceFirestore containing InvoiceDetails.

    Returns:
        Dictionary with invoice ID and a success message.
    """
    db = firestore.AsyncClient()
    invoice_details = create_invoice_data.invoice_details

    # Check if the invoice already exists
    invoice_ref = db.collection('draft_invoice').document(org).collection(invoice_details.file_name).document(invoice_details.invoiceId)
    existing_invoice = await invoice_ref.get()
    if existing_invoice.exists:
        return {
            "invoice_id": invoice_details.invoiceId,
            "message": "Invoice already exists, not creating a new one."
        }

    if await check_invoice_exists(org, invoice_details.file_name):
        docs = await db.collection('draft_invoice').document(org).collection(invoice_details.file_name).get()
        if docs:
            customer_id = docs[0].to_dict().get("customer_id")
        else:
            customer_id = str(uuid.uuid4()) # Handle case where no documents are found
    else:
        customer_id = str(uuid.uuid4())

    formatted_invoice = {
        'file_name': invoice_details.file_name,
        'invoice_id': invoice_details.invoiceId, # Keeping the general invoice_id
        'tran_id': invoice_details.tranId, # NetSuite tranId
        'tran_date': invoice_details.tranDate, # NetSuite tranDate
        'entity': invoice_details.entity, # NetSuite entity (Customer Name or ID)
        'currency': invoice_details.currency, # NetSuite currency
        'due_date': invoice_details.dueDate, # NetSuite dueDate
        'memo': invoice_details.memo, # NetSuite memo
        'line_items': [
            {
                'description': item.description,
                'quantity': item.quantity,
                'rate': item.rate,
                'amount': item.amount,
                'item': item.item, # NetSuite itemPDF text and parsed
                'location': item.location, # NetSuite location for line item
                'department': item.department, # NetSuite department for line item
                'subsidiary': item.subsidiary, # NetSuite subsidiary for line item
                'sales_rep': item.salesRep, # NetSuite sales rep for line item
                'terms': item.terms # NetSuite terms for line item
            }
            for item in invoice_details.itemList
        ],
        'order_id': invoice_details.orderId,
        'customer_id': customer_id,
        'invoice_location': invoice_details.location, # NetSuite location for invoice header
        'invoice_department': invoice_details.department, # NetSuite department for invoice header
        'invoice_subsidiary': invoice_details.subsidiary, # NetSuite subsidiary for invoice header
        'invoice_sales_rep': invoice_details.salesRep, # NetSuite sales rep for invoice header
        'invoice_terms': invoice_details.terms, # NetSuite terms for invoice header
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': "pending validation",
        'organization': org
    }

    invoice_ref = db.collection('draft_invoice').document(org).collection(invoice_details.file_name).document(invoice_details.invoiceId)
    await invoice_ref.set(formatted_invoice)

    return {
        "invoice_id": invoice_ref.id,
        "message": "Invoice created successfully"
    }

async def store_initial_invoice_data(create_invoice_data: CreateInvoiceFirestore, email: str, org: str):
    """ Stores invoice data in Firestore under initial_data/{org}/initial_invoice/{file_name} using the new InvoiceDetails schema.

    Args:
        create_invoice_data: An instance of CreateInvoiceFirestore containing InvoiceDetails.

    Returns:
        Dictionary with a success message.
    """
    db = firestore.AsyncClient()
    invoice_details = create_invoice_data.invoice_details

    # Create a reference to the initial_data collection
    invoice_ref = db.collection('initial_data').document(org).collection('initial_invoice').document(invoice_details.file_name)

    # Store the invoice details in Firestore
    formatted_invoice = {
        'file_name': invoice_details.file_name,
        'invoice_id': invoice_details.invoiceId,
        'tran_id': invoice_details.tranId, # NetSuite tranId
        'tran_date': invoice_details.tranDate, # NetSuite tranDate
        'entity': invoice_details.entity, # NetSuite entity (Customer Name or ID)
        'currency': invoice_details.currency, # NetSuite currency
        'due_date': invoice_details.dueDate, # NetSuite dueDate
        'memo': invoice_details.memo, # NetSuite memo
        'line_items': [
            {
                'description': item.description,
                'quantity': item.quantity,
                'rate': item.rate,
                'amount': item.amount,
                'item': item.item, # NetSuite item
                'location': item.location, # NetSuite location for line item
                'department': item.department, # NetSuite department for line item
                'subsidiary': item.subsidiary, # NetSuite subsidiary for line item
                'sales_rep': item.salesRep, # NetSuite sales rep for line item
                'terms': item.terms # NetSuite terms for line item
            }
            for item in invoice_details.itemList
        ],
        'order_id': invoice_details.orderId,
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': invoice_details.status,
        'organization': org
    }

    await invoice_ref.set(formatted_invoice)

    return {
        "message": "Invoice created successfully"
    }
