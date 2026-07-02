import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_message(phone_number: str, message: str="Welcome to Smart Queue App, Thx for Registering with us.") -> bool:
    """
    Send a 6-digit verification code via SMS.
    Routes to console (dev) or Infobip (production) based on SMS_BACKEND setting.
    """
    backend = getattr(settings, "SMS_BACKEND", "console")

    if backend == "console":
        return _console_backend(phone_number, message)
    elif backend == "infobip":
        return _infobip_backend(phone_number, message)
    elif backend == "twilio":
        return _twilio_backend(phone_number, message)
    elif backend == "twilio_whatsapp":
        return _twilio_whatsapp_backend(phone_number, message)
    else:
        logger.error(f"Unknown SMS_BACKEND: '{backend}'")
        return False


def _console_backend(phone_number: str, message: str) -> bool:
    """Development: print to console. No packages needed."""
    print("\n" + "=" * 50)
    print(f"📱 SMS TO : {phone_number}")
    print(f"   MESSAGE: {message}")
    print("=" * 50 + "\n")
    return True


def _infobip_backend(phone_number: str, message: str) -> bool:
    """
    Production: Infobip SMS API.
    Docs: https://www.infobip.com/docs/api/channels/sms/sms-messaging/outbound-sms/send-sms-message
    """
    url = f"https://{settings.INFOBIP_BASE_URL}/sms/2/text/advanced"

    headers = {
        "Authorization": f"App {settings.INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "messages": [
            {
                "destinations": [{"to": phone_number}],
                "from": getattr(settings, "INFOBIP_SENDER", "SmartQueue"),
                "text": message,
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        msg_status = data["messages"][0]["status"]
        status_name = msg_status.get("name", "UNKNOWN")

        if status_name in ("PENDING_ENROUTE", "PENDING_ACCEPTED", "MESSAGE_ACCEPTED"):
            logger.info(f"Infobip SMS queued for {phone_number} — status: {status_name}")
            return True
        else:
            logger.warning(f"Infobip unexpected status for {phone_number}: {msg_status}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Infobip SMS timeout for {phone_number}")
        return False
    except requests.exceptions.HTTPError as exc:
        logger.error(f"Infobip HTTP error for {phone_number}: {exc.response.status_code} — {exc.response.text}")
        return False
    except Exception as exc:
        logger.error(f"Infobip SMS failed for {phone_number}: {exc}")
        return False

def _twilio_backend(phone_number: str, message: str) -> bool:
    """
    Production: Twilio SMS API via native REST requests.
    Docs: https://www.twilio.com/docs/sms/api/message-resource
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    # Twilio API messages endpoint URL layout
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    # Twilio expects form-urlencoded parameters
    payload = {
        "To": phone_number,
        "From": settings.TWILIO_PHONE_NUMBER,
        "Body": message,
    }

    try:
        # Pass (account_sid, auth_token) to auth tuple to automatically build HTTP Basic headers
        response = requests.post(
            url, 
            data=payload, 
            auth=(account_sid, auth_token), 
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        status_name = data.get("status")

        # Valid states for an accepted dispatch are queued, scheduled, sending, or delivered
        if status_name in ("queued", "sending", "delivered"):
            logger.info(f"Twilio SMS accepted for {phone_number} — status: {status_name}")
            return True
        else:
            logger.warning(f"Twilio unexpected delivery state for {phone_number}: {status_name}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Twilio SMS timeout for {phone_number}")
        return False
    except requests.exceptions.HTTPError as exc:
        logger.error(f"Twilio HTTP error for {phone_number}: {exc.response.status_code} — {exc.response.text}")
        return False
    except Exception as exc:
        logger.error(f"Twilio SMS failed for {phone_number}: {exc}")
        return False
    
def _twilio_whatsapp_backend(phone_number: str, message: str) -> bool:
    """
    Production/Testing: Twilio WhatsApp Business API.
    Docs: https://www.twilio.com/docs/whatsapp/api
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    # Twilio uses the identical Messages endpoint for WhatsApp
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    # CRITICAL: Both numbers must be prefixed with "whatsapp:"
    formatted_to = f"whatsapp:{phone_number}"
    formatted_from = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"

    payload = {
        "To": formatted_to,
        "From": formatted_from,
        "Body": message,
    }

    try:
        response = requests.post(
            url, 
            data=payload, 
            auth=(account_sid, auth_token), 
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        status_name = data.get("status")

        if status_name in ("queued", "sending", "delivered"):
            logger.info(f"Twilio WhatsApp accepted for {phone_number} — status: {status_name}")
            return True
        else:
            logger.warning(f"Twilio WhatsApp unexpected state for {phone_number}: {status_name}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Twilio WhatsApp timeout for {phone_number}")
        return False
    except requests.exceptions.HTTPError as exc:
        logger.error(f"Twilio WhatsApp HTTP error: {exc.response.status_code} — {exc.response.text}")
        return False
    except Exception as exc:
        logger.error(f"Twilio WhatsApp failed for {phone_number}: {exc}")
        return False
