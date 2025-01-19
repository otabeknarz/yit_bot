import random
import string


def generate_custom_uuid(length=10):
    characters = string.ascii_letters + string.digits
    custom_uuid = "".join(random.choice(characters) for _ in range(length))
    return custom_uuid


# custom_uuid = generate_custom_uuid(10)
# print(f"Custom UUID: {custom_uuid}")
