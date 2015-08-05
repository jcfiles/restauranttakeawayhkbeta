from flask import Flask, render_template, url_for, request, redirect, jsonify, flash, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from restaurant_takeaway_setup import Base, Restaurant, MenuItem, Customer, Staff, CustomerOrder, CustomerOrderedItem
import os
import random
import paypalrestsdk

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'paypalrestapitest')
app = Flask('myapp', template_folder=tmpl_dir)

# Set secret key directly on the app to solve the flash problem
app.secret_key = 'many random bytes'

access_token = "asdf"
# Test paypalrestsdk request access token
@app.route('/getaccesstoken')
def getaccesstoken():
    global access_token
    api = paypalrestsdk.set_config(
      mode="sandbox", # sandbox or live
      client_id="AUkSDlXcL3qKVW8Yq45p4jlOjsDCBRGxCBHpATn4t8H0Ka8Q02DxkUxvdmVz-MazblfTjvCMd-5cC-EM",
      client_secret="EE7coF-C74aXMGEpm8hY-46yoXlr04oRGjVjk50vqVm83AoheJTzWwxdx1EmGGTDlLoiQtJnkVYtNUgD")
    access_token = api.get_access_token()
    return "access token = " + str(access_token) + "<p><a href='/checkoutpage'>Checkout page</a></p>"

@app.route('/checkoutpage')
def checkoutpage():
    return render_template('checkout.html')

@app.route('/createpayment/<int:payment_amount>')
def createpayment(payment_amount):
    global access_token
    api = paypalrestsdk.set_config(
      mode="sandbox", # sandbox or live
      client_id="AUkSDlXcL3qKVW8Yq45p4jlOjsDCBRGxCBHpATn4t8H0Ka8Q02DxkUxvdmVz-MazblfTjvCMd-5cC-EM",
      client_secret="EE7coF-C74aXMGEpm8hY-46yoXlr04oRGjVjk50vqVm83AoheJTzWwxdx1EmGGTDlLoiQtJnkVYtNUgD")
    access_token = api.get_access_token()
    payment = paypalrestsdk.Payment({
  "intent": "sale",
  "payer": {
    "payment_method": "paypal" },
  "redirect_urls": {
    "return_url": "http://localhost:5000/executepaymentrequest",
    "cancel_url": "http://localhost:5000/checkoutpage" },

  "transactions": [ {
    "amount": {
      "total": payment_amount,
      "currency": "USD" },
    "description": "creating a payment of " + str(payment_amount) } ] } )

    payment_response = payment.create()
    if payment_response == True:
        return "payment created. <p>payment: " + str(payment) + "</p>Payment amount: " + str(payment_amount) + "<p>Payment redirect_url: " + str(payment['links'][1]["href"]) + "</p>" + "<p>access token = " + str(access_token) + "</p>"
    if payment_response == False:
        return "payment not created"

@app.route('/executepaymentrequest')
def executepaymentrequest():
    payerID = request.args['PayerID']
    paymentID = request.args['paymentId']
    token = request.args['token']
    payment = paypalrestsdk.Payment.find(paymentID)
    payment.execute({"payer_id": payerID})
    return "payment object: " + str(payment) + "<p>payment ID: " + str(paymentID) + "</p><p>payerID: " + str(payerID) + "</p>"
    
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)