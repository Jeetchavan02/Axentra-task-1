REGISTER = {
    "summary": "Register a company",
    "description": "Creates a new company and its first user. Returns 409 if the email is taken.",
}

LOGIN = {
    "summary": "Log in",
    "description": (
        "Returns a JWT access token. Copy it into the **Authorize** button to call protected "
        "endpoints."
    ),
}

ME = {
    "summary": "Current user",
    "description": "Returns the logged-in user. Requires a valid token.",
}
