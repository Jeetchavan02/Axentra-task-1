ASSIGN = {
    "summary": "Assign a seat",
    "description": (
        "Gives an employee a seat. Returns 409 if the plan is full or not active, or if the "
        "employee already has this seat."
    ),
}
LIST = {"summary": "List seats", "description": "Paginated list of who holds a seat on this plan."}
REMOVE = {"summary": "Remove a seat", "description": "Frees the seat held by this employee."}
