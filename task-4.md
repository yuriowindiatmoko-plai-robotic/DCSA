# Context
We are implementing a new feature called "4. Create order special". This feature allows specific users to create special catering orders via a custom modal flow.

## 1. Frontend UI Implementation
- **Component:** Create a new component for the "Create Special Order" button.
- **Placement:** Position the button **above** the dashboard table div.
  - **Alignment:** It should be symmetrically situated **between** the Dashboard Filter div and dashboard table div, and the right side of the Side Tab.
- **Interaction:** Clicking this button opens a Modal form.

## 2. Modal Form Fields & Validation
The modal should contain the following input fields:
1. **Serving Date (`serving_date`)**: A date picker to select "H-Day" (the day the food will be served).
2. **Menu Details**: A section containing 3 specific categories. Each category requires a name and a quantity (total portions) same as like the order form before:
   - Snack
   - Heavy Meals
   - Beverages
3. **Dropping Location (`dropping_location_food`)**: A text input or select dropdown for the delivery location.
4. **Staff Allocation (Simplified)**:
   - Instead of a complex form, use simplified inputs that map to this specific JSON structure:
     ```json
     {
       "all_guest": {
         "total": 20, 
         "serving_type": "prasmanan", 
         "drop_off_location": "Pantry"
       }
     }
     ```
   - *Note:* Only one entry is needed here, hardcoded to the key `all_guest`. Form inputs should allow editing the `total`, `serving_type`, and `drop_off_location`.

## 3. API Payload Structure
When the form is submitted, construct the JSON payload as follows:
- **`order_type`**: Hardcoded to the string `"SPECIAL"` (do not expose this in the UI).
- **`status`**: Determine based on the current user's role (see Logic below).
- **`staff_allocation`**: Use the structure defined above.

/api/orders/

query Parameters
using created_by string($uuid) (query) Creator user ID

{
  "order_date": "2026-01-14", -> serving_date
  "order_type": "SPECIAL",
  "total_portion": 0, -> total_portion
  "staff_allocation": {
    "all_guest": {
      "total": 0,
      "drop_off_location": "string",
      "serving_type": "string"
    }
  },
  "menu_details": {
    "heavy_meal": [],
    "snack": [],
    "beverages": []
  },
  "dropping_location_food": "string",
  "special_notes": "string",
  "institution_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", -> institution_id from users login
}


## 4. Business Logic (Role-Based Status)
Implement logic to set the `status` field automatically based on the authenticated user's role upon submission:
- **If Role is `client_admin`**: Set status to **`DRAFT`**.
- **If Role is `dk_admin` OR `super_admin`**: Set status to **`ORDERED`**.

but these are have some technical debts, because the endpoint to create order doesn't have the accommodate the status like 'DRAFT', 'REQUEST_TO_EDIT', 'APPROVED_EDITED', 'APPROVED', 'REJECTED', 'NOTED', 'PROCESSING', 'COOKING', 'READY', 'DELIVERED', 'ORDERED'. 
but then the status is varchar(50) DEFAULT 'DRAFT'::character varying NOT NULL, , so that it directly handle by database. so that i think we should just make dk_admin OR super_admin same as client_admin which is set to DRAFT. because then dk_admin OR super_admin will be able change the status after that the order is created.



## 5. Technical Constraints
- Please use the existing project's styling conventions (vue3 + Tailwind CSS / Material UI / Bootstrap, depending on your stack).
- Ensure the Modal is responsive.
- Do not modify the Side Tab or Filter layout; strictly insert the new button component in the specified gap.