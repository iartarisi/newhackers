import re

def valid_url(url):
    """Returns True if the :url: string is a valid URL, False otherwise"""
    # This code was copied from the Django project's django.core.validators
    # which is available under a BSD License
    regex = re.compile(
        r'^(?:http|ftp)s?://'                             # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'            # domain...
        r'localhost|'                                     # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'            # ...or ip
        r'(?::\d+)?'                                      # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if regex.match(url):
        return True
    else:
        return False
