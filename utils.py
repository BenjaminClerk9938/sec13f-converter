import re

def clean_text(text):
    # Remove unwanted characters or patterns from text
    cleaned_text = re.sub(r'\s+', ' ', text.strip())
    return cleaned_text
