from twilio.rest import TwilioRestClient 
 
# put your own credentials here 
ACCOUNT_SID = "AC520e6dbbf749f6dc281290fe7503b139" 
AUTH_TOKEN = "2a85f23a45bddd4ae5590db89069051f" 
 
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 
 
client.messages.create(
    to="+447768234908", 
    from_="+441158243132", 
    body="Your takeaway items are on the way!" + "Amount paid = $" + str(123),  
)