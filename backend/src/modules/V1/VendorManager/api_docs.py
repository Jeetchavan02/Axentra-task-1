CREATE = {
    "summary": "Create a vendor",
    "description": "Returns 409 if your company already has a vendor with this name.",
}
LIST = {
    "summary": "List vendors",
    "description": "Paginated. `search` matches part of the name, ignoring case.",
}
GET = {"summary": "Get a vendor", "description": "Returns 404 if it isn't in your company."}
UPDATE = {"summary": "Update a vendor", "description": "Replaces the vendor's name and website."}
DELETE = {
    "summary": "Delete a vendor",
    "description": "Returns 409 if the vendor still has subscriptions.",
}
