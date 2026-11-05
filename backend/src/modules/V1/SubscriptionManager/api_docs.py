CREATE = {
    "summary": "Create a subscription",
    "description": (
        "`price` is per billing cycle. Returns 404 if the vendor isn't in your company, "
        "and 409 if that vendor already has this plan."
    ),
}
LIST = {
    "summary": "List subscriptions",
    "description": "Paginated. Filter by `status` or `vendor_id`; `search` matches the plan name.",
}
GET = {"summary": "Get a subscription", "description": "Returns 404 if it isn't in your company."}
UPDATE = {
    "summary": "Update a subscription",
    "description": "Replaces all fields. Returns 409 if `seat_limit` is below the seats in use.",
}
DELETE = {
    "summary": "Delete a subscription",
    "description": "Returns 409 if the subscription still has seats assigned.",
}
