#!/bin/bash

curl -X POST \
  http://localhost:8000/api/v1/validation/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "workflow_id": "bb14c848-6891-4550-a7c8-a61050bb699a",
    "corrected_data": {
      "payment_terms": {
        "amount": 15000,
        "currency": "INR",
        "frequency": "monthly",
        "due_days": 30,
        "late_fee": 500,
        "payment_method": "bank_transfer"
      },
      "client": {
        "name": "Narayana",
        "email": "client@example.com",
        "address": "Laxmi Leela ground floor 3rd cross Ayyappa Nagar behind Ayyappa Temple, Jalahalli West, Bangalore - 15",
        "phone": "+91-9876543210",
        "tax_id": "GST123456789",
        "role": "client"
      },
      "service_provider": {
        "name": "Kuttan",
        "email": "ramshaiqbal4@gmail.com",
        "address": "site No 152 Geethalayam OMH colong S.M. Road 1st main, T.Dasarahalli, Bangalore-57",
        "phone": "9555369500",
        "tax_id": "GST987654321",
        "role": "service_provider"
      },
      "services": [
        {
          "description": "Rental of premises at site No. 820 S.M. Road, Jalahalli West, Bangalore - 15, approximate 500 sft area of IInd floor with A.C. Sheet roof.",
          "quantity": 1,
          "unit_price": 15000,
          "total_amount": 15000,
          "unit": "monthly"
        }
      ]
    },
    "user_notes": "Corrected rental agreement data"
  }'
