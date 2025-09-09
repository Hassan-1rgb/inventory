from twilio.rest import Client

# Your Twilio credentials
account_sid = "ACcfec7d1d0cc6571429e86e39523a4ddb"
auth_token = "cdc501afe5f3c3b9c70f69ff45a2c590"
verify_sid = "VA276fcca9d559a1b41f06238b2ad67bb4"

client = Client(account_sid, auth_token)

try:
    verification = client.verify.v2.services(verify_sid).verifications.create(
        to='+923244844104',  # Your actual phone number
        channel='sms'
    )
    print("OTP sent. Status:", verification.status)
except Exception as e:
    print("Failed to send OTP:", e)
