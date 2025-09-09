
from twilio.rest import Client
from django.conf import settings

def send_otp_via_twilio(phone_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    verification = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
        to=phone_number,
        channel='sms'
    )
    return verification.status  