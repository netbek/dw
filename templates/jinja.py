from jinja2.ext import Extension

import secrets
import string


def generate_password(length=32):
    # Quotes are excluded so that quoted values can be used in .env files.
    # $ is excluded because it causes variable substition in some cases.
    special_chars = "!;#%&()*+,-./:;<=>?@[]^_{|}~"
    alphabet = string.ascii_letters + string.digits + special_chars

    # Ensure the first character is a letter
    first_char = secrets.choice(string.ascii_letters)
    other_chars = [
        secrets.choice(string.ascii_lowercase),  # At least one lowercase letter
        secrets.choice(string.ascii_uppercase),  # At least one uppercase letter
        secrets.choice(string.digits),  # At least one digit
        secrets.choice(special_chars),  # At least one special character
    ]
    other_chars += [secrets.choice(alphabet) for _ in range(length - len(other_chars) - 1)]
    secrets.SystemRandom().shuffle(other_chars)
    password = first_char + "".join(other_chars)

    return password


class GeneratePassword(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["generate_password"] = generate_password
