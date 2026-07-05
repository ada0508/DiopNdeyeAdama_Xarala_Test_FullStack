import hmac
import hashlib
from django.conf import settings

def verify_signature(payload_body, received_signature):
    # 1. Je refais le melange de mon cote : message + secret → code
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    # 2. Je compare mon code avec celui recu dans le message
    return hmac.compare_digest(expected, received_signature)