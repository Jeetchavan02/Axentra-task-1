CREATE = {
    "summary": "Create an employee",
    "description": "Returns 409 if your company already has an employee with this email.",
}
LIST = {
    "summary": "List employees",
    "description": "Paginated. `search` matches part of the name or email, ignoring case.",
}
GET = {"summary": "Get an employee", "description": "Returns 404 if they aren't in your company."}
UPDATE = {"summary": "Update an employee", "description": "Replaces the name and email."}
DELETE = {
    "summary": "Delete an employee",
    "description": "Returns 409 if the employee still holds seats.",
}
