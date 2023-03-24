import re


def extract_phone_number(text):
    """Extracts a phone number with international code from a text that starts with "whatsapp:".

    Args:
        text (str): The text to search for a phone number.

    Returns:
        str: A string representing the phone number with international code if found, or an empty string otherwise.

    Examples:
        >>> extract_phone_number("This is a message with a whatsapp:+15551234567 phone number")
        '+15551234567'
    """
    # Regular expression pattern for matching phone numbers that start with "whatsapp:"
    pattern = r"\bwhatsapp:(\+[\d]{1,3}\s?)?(\d{10,14})\b"

    # Find the phone number in the text using the pattern
    match = re.search(pattern, text)

    # Get the phone number and international code as strings
    if match:
        international_code = match.group(1).strip() if match.group(1) else ""
        phone_number = match.group(2)

        # Return the phone number with international code as a single string
        return f"{international_code}{phone_number}"


if __name__ == "__main__":
    phone_number = extract_phone_number("whatsapp:+15551234567")
    print(phone_number)
