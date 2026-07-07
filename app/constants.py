"""App-wide constants."""

# (name, color) seeded for every new user; user_id stays NULL on the template
# row, per-user copies are created in auth_service.register_user.
DEFAULT_CATEGORIES: list[tuple[str, str]] = [
    ("Alimentação", "#D97757"),
    ("Transporte", "#3B82F6"),
    ("Moradia", "#0D9488"),
    ("Saúde", "#E11D48"),
    ("Lazer", "#8B5CF6"),
    ("Educação", "#F59E0B"),
    ("Outros", "#64748B"),
]
