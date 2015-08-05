from flask import Flask, render_template, url_for, request, redirect, jsonify, flash, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from restaurant_takeaway_setup import Base, Restaurant, MenuItem, Customer, Staff, CustomerOrder, CustomerOrderedItem
import os, random, paypalrestsdk

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webpages')
app = Flask('myapp', template_folder=tmpl_dir)

# Set secret key directly on the app to solve the flash problem
app.secret_key = 'many random bytes'

# Initialize link with restaurant takeaway system database
engine = create_engine('sqlite:///restaurant_takeaway_system.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create fake objects of restaurants
restaurant = {'id':1,'name':'Ming Fat Restaurant'}
restaurant_two = {'id':2,'name':'278 Restaurant'}
restaurant_three = {'id':3,'name':'fusion'}
restaurants = [restaurant,restaurant_two,restaurant_three]

# Create fake objects of menuitems
menuitem = {'name':'king prawn noodles',
             'id':1,
             'description':'tasty king prawn noodles with salt',
             'price':2,
             'restaurant_id':1}
menuitem_two = {'name':'spaghetti with brown sauce',
                'id':2,
                'description':'boiled spaghetti with French taste',
                'price':3,
                'restaurant_id':2}
menuitem_three = {'name':'beef sirloin',
                'id':3,
                'description':'7oz beef sirloin with original Argentinian-imported oyster sauce',
                'price':5,
                'restaurant_id':3}
menuitems = [menuitem,menuitem_two,menuitem_three]

# Create fake objects of customers
customer = {'name':'Mr A',
             'id':1,
             'order_time':'2015-01-01 00:00:00',
             'menuitem_id':1,
             'restaurant_id':1}
customer_two = {'name':'Mr B',
                'id':2,
                'order_time':'2016-01-01 00:00:00',
                'menuitem_id':2,
                'restaurant_id':2}
customer_three = {'name':'Mr C',
                'id':3,
                'order_time':'2017-01-01 00:00:00',
                'menuitem_id':3,
                'restaurant_id':3}
customers = [customer,customer_two,customer_three]

# Create fake objects of staff
staff = {'name':'Ventila Quron',
         'id':1,
         'restaurant_id':1}

import hashlib
def makehash(username, password): 
    return hashlib.sha256(username+password+"secret").hexdigest()

def makecustomerorderhash(customerorder_id):
    return hashlib.sha256(str(customerorder_id)+"secret").hexdigest()

def randomNumberGenerator():
    return random.randint(0,1000)

@app.route('/')
@app.route('/mainpage')
def mainPage():
    return render_template('mainpage.html')

customer_verification_code_preset = 0

@app.route('/customersignup', methods=['GET','POST'])
def customersignup():
    global customer_verification_code_preset
    if request.method=='GET':
        customer_verification_code_preset = randomNumberGenerator()
        return render_template('customer_signup.html',randNumber=customer_verification_code_preset)
    if request.method=='POST':
        customer_username = request.form['username']
        customer_password = request.form['password']
        customer_reconfirm_password = request.form['reconfirm_password']
        customer_first_name = request.form['firstname']
        customer_surname = request.form['surname']
        customer_phone_number = request.form['phone_number']
        customer_delivery_address = request.form['preferred_delivery_address']
        user_input_verification_code = request.form['verification_code']
        try:
            user_input_verification_code = int(user_input_verification_code)
            if user_input_verification_code != (customer_verification_code_preset + 8):
                flash("wrong verification code, please try again")
                return redirect("customersignup")
        except:
            flash("wrong verification code, please try again")
            return redirect("customersignup")
        if customer_password != customer_reconfirm_password:
            flash("password mismatch")
            return redirect('customersignup')
        if session.query(Customer).filter_by(username=customer_username).scalar():
            flash("username already taken")
            return redirect('customersignup')
        # if phone number is not made of digits (i.e. use regex), then fuck off...
        if customer_phone_number.isdigit() == False:
            flash("phone number does not only contain digits")
            return redirect('customersignup')
        customer_hashed_password = makehash(customer_username,customer_password)
        new_customer = Customer(username=customer_username,password=customer_hashed_password,first_name=customer_first_name,surname=customer_surname,phone_number=customer_phone_number,preferred_delivery_address=customer_delivery_address)
        session.add(new_customer)
        flash("customer " + customer_username + " created.")
        session.commit()
        return redirect('customerlogin')


@app.route('/customerlogin', methods=['GET','POST'])
def customerlogin():
    if request.method=='GET':
        return render_template('customer_login.html')
    if request.method=='POST':
        customer_username = request.form['username']
        customer_password = request.form['password']
        customer_hashed_password = makehash(customer_username, customer_password)
        
        # Below all_customers variable is used to see whether there are more than 1 users having the same username
        all_customers = session.query(Customer).filter_by(username=customer_username,
                                                     password=customer_hashed_password).all()
        if len(all_customers) > 1:
            for customer in all_customers:
                print "customer.username + str(customer.id): " + customer.username + str(customer.id)
                
        customer = session.query(Customer).filter_by(username=customer_username,
                                                     password=customer_hashed_password).scalar()
        
        if customer:
            flash("Login success for " + str(customer_username))
            resp = make_response(redirect('customerloginsuccess'))
            resp.set_cookie('customer_id', str(customer.id) )
            resp.set_cookie('customer_hash', customer.password)
            return resp
        return redirect('customerlogin')

@app.route('/showallcustomers')
def showallcustomers():
    return render_template('showallcustomers.html',customers=session.query(Customer).all())

@app.route('/showallmenuitems')
def showallmenuitems():
    return render_template('showallmenuitems.html',menuitems=session.query(MenuItem).all())

def checkCustomerCookie():
    customer_cookie_id = request.cookies.get("customer_id")
    customer_cookie_hashed_password = request.cookies.get("customer_hash")
    customer = session.query(Customer).filter_by(id=customer_cookie_id).scalar()
    if not customer:
        flash ("not logged in")
        return redirect('customerlogin')
    if customer_cookie_hashed_password == customer.password:
        return customer
    else:
        return None

def checkCustomerOrderCookie():
    customer_order_id = request.cookies.get("customer_order_id")
    customerorderhash_in_cookie = request.cookies.get("customerorderhash")

    # make customer_order_id a float variable
    customer_order_id = float(customer_order_id)
    customerorder = session.query(CustomerOrder).filter_by(id=customer_order_id,customerorderhash=customerorderhash_in_cookie).scalar()
    if not customerorder:
        flash ("no customer order")
        return redirect('orderfoodpage')
    if customerorderhash_in_cookie == customerorder.customerorderhash:
        return customerorder
    else:
        return None

@app.route('/customerloginsuccess')
def customerloginsuccess():
    if checkCustomerCookie():
        return render_template('customerloginsuccess.html',customer=checkCustomerCookie())
    else:
        return redirect("customerlogin")

import datetime

@app.route('/orderfoodpage', methods=['GET','POST'])
def orderfoodpage():
    if request.method=='GET':
        restaurants = session.query(Restaurant).all()
        menuitems = session.query(MenuItem).all()
        if checkCustomerCookie():
            return render_template('orderfoodpage.html',restaurants=restaurants,menuitems=menuitems,customer=checkCustomerCookie())
        else:
            return redirect("customerlogin")
    if request.method=='POST':
        if checkCustomerCookie():
            customer = checkCustomerCookie()
            # add customerorder into sqlalchemy database
            customerorder = CustomerOrder(customer_id=customer.id,customer_username=customer.username,place_order_time = datetime.datetime.now(),completion_status=False)
            session.add(customerorder)
            session.commit()

            # generate customer order hash and add it to database
            customerorder.customerorderhash = makecustomerorderhash(customerorder.id)
            session.add(customerorder)
            session.commit()

            # add customerordereditems into sqlalchemy database
            menuitem_ids = request.form.getlist('menuitem_id')
            
            if not menuitem_ids:
                flash("please select a few menu items")
                return redirect(url_for('orderfoodpage',customer_id=customer.id))
            price_of_a_customerorder = 0
            for menuitem_id in menuitem_ids:
                menuitem = session.query(MenuItem).filter_by(id=menuitem_id).scalar()
                customerordereditem = CustomerOrderedItem(menuitem_id=menuitem_id,
                                                        menuitem_price = menuitem.price,
                                                          restaurant_id=menuitem.restaurant_id,
                                                          customer_id=customer.id,
                                                          customerorder_id=customerorder.id)
                
                session.add(customerordereditem)
                session.commit()

                # sum up the total price of every menu item
                price_of_a_customerorder = menuitem.price

                customerorder.restaurant_id = menuitem.restaurant_id
                session.add(customerorder)
                session.commit()

            # sum up the total price of every menu item, and add it to customerorder
            customerorder.total_price = price_of_a_customerorder
            # set cookie attribute for customer order
            session.add(customerorder)
            session.commit()
            resp = make_response(redirect('cart'))
            resp.set_cookie('customer_order_id', str(customerorder.id) )
            resp.set_cookie('customerorderhash', str(customerorder.customerorderhash) )
            resp.set_cookie('customer_order_status', 'incomplete' )
            return resp
        else:
            flash("not logged in")
            return redirect("customerlogin")
        

@app.route('/showallcustomerordereditems')
def customerordereditems():
    customerordereditems = session.query(CustomerOrderedItem).all()
    customerordereditems_list = []
    for customerordereditem in customerordereditems:
        customerordereditems_list.append(customerordereditem.customerorder_id)
    return str(customerordereditems_list)

def checkCustomerOrderStatusCookie():
    status = request.cookies.get("customer_order_status")
    if not status:
        flash ("error. customer_order_status not found")
        return redirect('orderfoodpage')
    return status

@app.route('/cart')
def cart():
    if checkCustomerCookie() and checkCustomerOrderCookie():
        customerorder = checkCustomerOrderCookie()
        customer = checkCustomerCookie()
        customerordereditems = session.query(CustomerOrderedItem).filter_by(customer_id=customer.id,customerorder_id=customerorder.id).all()
        cartitems = []
        restaurants = []
        for customerordereditem in customerordereditems:
            menuitem = session.query(MenuItem).filter_by(id=customerordereditem.menuitem_id).scalar()
            cartitems.append(menuitem)

            # add restaurants into output
            restaurant = session.query(Restaurant).filter_by(id=customerordereditem.restaurant_id).scalar()
            restaurants.append(restaurant)

        return render_template('cart.html',cartitems=cartitems,customer=customer,total_pay_amount=customerorder.total_price,restaurants=restaurants)
    else:
        flash("not logged in or no customer order")
        return redirect('customerlogin')

@app.route('/checkout')
def checkout():
    if checkCustomerCookie() and checkCustomerOrderCookie():
        customer = checkCustomerCookie()
        customerorder = checkCustomerOrderCookie()
        customerordereditems = session.query(CustomerOrderedItem).filter_by(customer_id=customer.id,customerorder_id=customerorder.id).all()
        cartitems = []
        restaurants = []

        # get total_pay_amount by reading the customerorder cookie
        total_pay_amount = customerorder.total_price
        print 'total_pay_amount of CustomerOrder ' + str(customerorder.id) + ' ' + str(customerorder.total_price)

        for customerordereditem in customerordereditems:
            menuitem = session.query(MenuItem).filter_by(id=customerordereditem.menuitem_id).scalar()
            cartitems.append(menuitem)

            # add restaurants into output
            restaurant = session.query(Restaurant).filter_by(id=customerordereditem.restaurant_id).scalar()
            restaurants.append(restaurant)

        return render_template('checkout.html',cartitems=cartitems,customer=customer,total_pay_amount=total_pay_amount,restaurants=restaurants)
    else:
        flash("not logged in or no customer order")
        return redirect('customerlogin')

@app.route('/customersettings')
def customersettings():
    if checkCustomerCookie():
        return render_template("customersettings.html",customer=checkCustomerCookie())
    else:
        flash("not logged in or no customer order")
        return redirect('customerlogin')



access_token = ""
@app.route('/createpayment', methods=['GET','POST'])
def createpayment():
    if request.method=='POST':
        if request.form["payment_amount"]:
            if checkCustomerOrderCookie():
                customerorder = checkCustomerOrderCookie()
                payment_amount = request.form['payment_amount']
                global access_token
                api = paypalrestsdk.set_config(
                  mode="sandbox", # sandbox or live
                  client_id="AUkSDlXcL3qKVW8Yq45p4jlOjsDCBRGxCBHpATn4t8H0Ka8Q02DxkUxvdmVz-MazblfTjvCMd-5cC-EM",
                  client_secret="EE7coF-C74aXMGEpm8hY-46yoXlr04oRGjVjk50vqVm83AoheJTzWwxdx1EmGGTDlLoiQtJnkVYtNUgD")
                access_token = api.get_access_token()
                payment = paypalrestsdk.Payment({
              "intent": "sale",

              "redirect_urls": {
                "return_url": "http://52.2.64.93:5000/executepaymentrequest",
                "cancel_url": "http://52.2.64.93:5000/checkout"
                
               },

              "payer": 
                {
                    "payment_method": "paypal" ,
                    "payer_info": 
                    {
                        "shipping_address": 
                        {
                            "line1": str(customerorder.customer_delivery_address),
                            "country_code": "HK"
                        }
                    }
                },

              "transactions": 
                    [ {
                    "amount": {
                      "total": payment_amount,
                      "currency": "USD" },
                    "description": "creating a payment of US$" + str(payment_amount),

                    } ], 

                } )
            
                payment_response = payment.create()
                if (payment_response == True) and (len(payment['links']) > 1):
                    return render_template("customercreatepayment.html",redirect_url=payment['links'][1]["href"])
                if payment_response == False:
                    return "payment not created"
            else:
                return "'customerordercookie' does not exist"
        else:
            return "payment_amount not passed in POST method"

from twilio.rest import TwilioRestClient     
@app.route('/executepaymentrequest')
def executepaymentrequest():
    # Paypal Rest API stuff
    payerID = request.args['PayerID']
    paymentID = request.args['paymentId']
    token = request.args['token']
    payment = paypalrestsdk.Payment.find(paymentID)
    payment.execute({"payer_id": payerID})
    
    # Twilio Rest API stuff
    ACCOUNT_SID = "AC520e6dbbf749f6dc281290fe7503b139" 
    AUTH_TOKEN = "2a85f23a45bddd4ae5590db89069051f" 
    print "payment['transactions']" + str(payment['transactions'])
     
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 
     
    client.messages.create(
        to="+447768234908", 
        from_="+441158243132", 
        body="Your takeaway items are on the way! \nPaymentID = " + str(paymentID),  
    )

    client.messages.create(
        to="+447768234908", 
        from_="+441158243132", 
        body="A customer has just placed a takeaway order on your restaurant. \nPaymentID = " + str(paymentID),  
    )


    # declare successful payment by declaring that the customer order is completed. 
    customerorder = checkCustomerOrderCookie()
    customerorder.completion_status = True
    session.add(customerorder)
    session.commit()

    # text to display in customerexecutepaymentsuccessful.html
    messageToReturn = "<h1>Payment successful</h1>payment object: " + str(payment) + "<p>payment ID: " + str(paymentID) + "</p><p>payerID: " + str(payerID) + "</p>"

    # declare customerorder's status as completed in cookies. 
    resp = make_response(render_template('customerexecutepaymentsuccessful.html',messageToReturn=messageToReturn))
    resp.set_cookie('customer_order_status', 'completed' )

    return resp

@app.route('/viewpurchasedfoodpage')
def viewpurchasedfoodpage():
    if checkCustomerCookie() and checkCustomerOrderCookie():
        customer = checkCustomerCookie()
        customerorder = checkCustomerOrderCookie()
        if not customerorder or not customer:
            flash("customerorder cookie or customer cookie does not exist")
            return redirect('customerlogin')
        total_price = customerorder.total_price
        customerordereditems = session.query(CustomerOrderedItem).filter_by(customer_id=customer.id,customerorder_id=customerorder.id).all()
        cartitems=[]
        restaurants=[]
        for customerordereditem in customerordereditems:
            menuitem = session.query(MenuItem).filter_by(id=customerordereditem.menuitem_id).scalar()
            cartitems.append(menuitem)

            # add restaurants to output. Only add a restaurant only if it does not exist in the existing "restaurants" list
            restaurant = session.query(Restaurant).filter_by(id=customerordereditem.restaurant_id).scalar()
            if restaurant not in restaurants:
                restaurants.append(restaurant)

        return render_template('viewpurchasedfoodpage.html',cartitems=cartitems,customer=customer,total_price=total_price,restaurants=restaurants)
    else:
        flash("not logged in or no customer order")
        return redirect('customerlogin')

@app.route('/customerpurchasehistory')
def customerpurchasehistory():
    if checkCustomerCookie():
        customer = checkCustomerCookie()
        if not customer:
            flash("customerorder cookie or customer cookie does not exist")
            return redirect('customerlogin')
        customerordereditems = session.query(CustomerOrderedItem).filter_by(customer_id=customer.id).all()
        
        # add cartitems, restaurants
        purchasedmenuitems=[]
        restaurants=[]
        customerorders = []

        for customerordereditem in customerordereditems:
            menuitem = session.query(MenuItem).filter_by(id=customerordereditem.menuitem_id).scalar()
            purchasedmenuitems.append(menuitem)

            # add restaurants to output. Only add a restaurant only if it does not exist in the existing "restaurants" list
            restaurant = session.query(Restaurant).filter_by(id=customerordereditem.restaurant_id).scalar()
            if restaurant not in restaurants:
                restaurants.append(restaurant)

            # add customerorders to output. Only add a customerorder only if it does not exist in the existing "customerorders" list
            customerorder = session.query(CustomerOrder).filter_by(customer_id=customer.id,id=customerordereditem.customerorder_id).scalar()
            if customerorder not in customerorders:
                customerorders.append(customerorder)

        return render_template('customerpurchasehistory.html',purchasedmenuitems=purchasedmenuitems,customer=customer,customerorders=customerorders,restaurants=restaurants)
    else:
        flash("not logged in")
        return redirect('customerlogin')

def checkStaffCookie():
    staff_cookie_id = request.cookies.get("staff_id")
    staff_cookie_hashed_password = request.cookies.get("staff_hash")
    staff = session.query(Staff).filter_by(id=staff_cookie_id).scalar()
    if staff == None:
        flash ("not logged in")
        return redirect('/stafflogin')
    if (staff_cookie_hashed_password == None) or (staff_cookie_id == None):
        return None
    if staff_cookie_hashed_password == staff.password:
        return staff
    else:
        return None

@app.route('/stafflogin', methods=['GET','POST'])
def stafflogin():
    if request.method=='GET':
        return render_template('staff_login.html')
    if request.method=='POST':
        staff_username = request.form['username']
        staff_password = request.form['password']
        staff_hashed_password = makehash(staff_username,staff_password)
        print '\n'
        print 'staff_username:' + staff_username + '\n'
        print 'staff_password:' + staff_password + '\n'
        print 'staff_hashed_password:' + staff_hashed_password
        staff = session.query(Staff).filter_by(username=staff_username,password=staff_hashed_password).scalar()
        if staff:
            flash("Login success for " + str(staff_username))
            response = make_response(redirect('/checkfoodorderstatus') )  
            response.set_cookie('staff_id',str(staff.id))
            response.set_cookie('staff_hash',staff_hashed_password )
            return response
        else:
            flash ("incorrect username or password.")
            return redirect('stafflogin')

staff_verification_code_preset = 0

@app.route('/staffsignup', methods=['GET','POST'])
def staffsignup():
    global staff_verification_code_preset
    if request.method=='GET':
        staff_verification_code_preset = randomNumberGenerator()
        print "staff_verification_code_preset: " + str(staff_verification_code_preset)
        return render_template('staff_signup.html',randNumber = staff_verification_code_preset)
    if request.method=='POST':
        staff_username = request.form['username']
        staff_password = request.form['password']
        staff_reconfirm_password = request.form['reconfirm_password']
        staff_email = request.form['email']
        staff_restaurant_id = int(request.form['restaurant_id'])
        user_input_verification_code = (request.form['verification_code'])
        try:
            user_input_verification_code = int(user_input_verification_code)
            print "user_input_verification_code: " + str(user_input_verification_code)
            print "staff_verification_code_preset: " + str(staff_verification_code_preset)
            if user_input_verification_code != (staff_verification_code_preset + 8):
                flash("wrong verification code, please try again")
                return redirect("staffsignup")
            if staff_password != staff_reconfirm_password:
                flash("password mismatch")
                return redirect('staffsignup')
            if session.query(Staff).filter_by(username=staff_username).scalar():
                flash("username already taken")
                return redirect('staffsignup')
            if not session.query(Restaurant).filter_by(id=staff_restaurant_id).scalar():
                flash("restaurant id " + str(id) + " does not exist")
                return redirect('staffsignup')
            hashed_staff_password = makehash(staff_username, staff_password) 
            new_staff = Staff(username=staff_username,password=hashed_staff_password,
                              restaurant_id=staff_restaurant_id,email=staff_email)
            session.add(new_staff)
            session.commit()
            flash("staff " + staff_username + " created.")
            return redirect('stafflogin')
        except:
            flash("wrong verification code, please try again")
            return redirect("staffsignup")   
        

@app.route('/checkfoodorderstatus', methods=['GET','POST'])
def checkfoodorderstatus():
    if checkStaffCookie():
        staff = checkStaffCookie()
        restaurant = session.query(Restaurant).filter_by(id=staff.restaurant_id).scalar()
        restaurant_id = restaurant.id
        if not restaurant:
            return redirect('stafflogin')

        # get all customers, customer orders, customer ordered items and all menuitems of a restaurant
        all_customers = session.query(Customer).all()
        all_customerOrders = session.query(CustomerOrder).filter_by(restaurant_id=restaurant_id).all()
        all_customerOrderedItems = session.query(CustomerOrderedItem).filter_by(restaurant_id=restaurant_id).all()
        all_menuItems = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
        
        all_customers_in_the_restaurant = []
        # need to get all_customers_in_the_restaurant
        for customer in all_customers:
            all_customerOrders_of_a_customer = session.query(CustomerOrder).filter_by(customer_id=customer.id,restaurant_id=restaurant_id).all()
            for customerOrders_of_a_customer in all_customerOrders_of_a_customer:
                if customer.id == customerOrders_of_a_customer.customer_id:
                    all_customers_in_the_restaurant.append(customer)
        
        customerorders_and_customerordereditems = {}
        customerOrderedItems_for_a_particular_customerorder = []
        # get all customerorders for that restaurant
        for customerorder in all_customerOrders:
            customerOrderedItems_for_a_particular_customerorder = session.query(CustomerOrderedItem).filter_by(restaurant_id=restaurant_id,customerorder_id=customerorder.id).all()
            customerorders_and_customerordereditems[customerorder.id] = customerOrderedItems_for_a_particular_customerorder

        # initialize all_menuitems_ordered_by_all_customers {} dictionary. Tell Python compiler it contains an array as its key. 
        all_menuitems_ordered_by_all_customers = {}
        for customer in all_customers_in_the_restaurant:
            all_menuitems_ordered_by_all_customers[customer.id] = []

        # for each customer order, assign the menuitem to the correct customer in all_menuitems_ordered_by_all_customers {} dictionary. 
        for customerOrderedItem in all_customerOrderedItems:
            for customer in all_customers_in_the_restaurant:
                if customerOrderedItem.customer_id == customer.id:
                     menuitem = session.query(MenuItem).filter_by(id=customerOrderedItem.menuitem_id).scalar()
                     print 'customer: ' + str(customer.username)
                     print 'menuitem.name: ' + str(menuitem.name)
                     all_menuitems_ordered_by_all_customers[customer.id].append(menuitem)
        
        if request.method=='GET':
            return render_template('checkfoodorderstatus.html',
                                   staff=staff,
                                   customers=all_customers_in_the_restaurant,
                                   restaurant=restaurant,
                                   menuitems=all_menuItems,
                                   customerorders_and_customerordereditems=customerorders_and_customerordereditems,customerorders=all_customerOrders)
    else:
        print 'not logged in'
        flash('not logged in')
        return redirect('stafflogin')

@app.route('/staffeditmenuitems', methods=['GET','POST'])
def staffeditmenuitems():
    if checkStaffCookie():
        staff = checkStaffCookie()
        if request.method=='GET':
            restaurant = session.query(Restaurant).filter_by(id=staff.restaurant_id).scalar()
            menuitems = session.query(MenuItem).filter_by(restaurant_id=staff.restaurant_id).all()
            if not restaurant:
                return redirect('/stafflogin')
            return render_template("staffeditmenuitems.html",menuitems=menuitems)
        if request.method=='POST':
            menuitem_id = request.form['menuitem_id']
            changed_menuitem_name = request.form['menuitem_name']
            changed_menuitem_price = request.form['menuitem_price']
            changed_menuitem_description = request.form['menuitem_description']
            menuitem = session.query(MenuItem).filter_by(id=menuitem_id,restaurant_id=staff.restaurant_id).scalar()
            menuitem.name = changed_menuitem_name
            menuitem.price = changed_menuitem_price
            menuitem.description = changed_menuitem_description
            session.add(menuitem)
            session.commit()
            return redirect('/staffeditmenuitems')
    else:
        print 'not logged in'
        flash('not logged in')
        return redirect('stafflogin')

@app.route('/logout')
def logoutpage():
    response = make_response(redirect('mainpage'))
    response.set_cookie('staff_id',expires=0)
    response.set_cookie('customer_id',expires=0)
    response.set_cookie('staff_hash',expires=0)
    response.set_cookie('customer_hash',expires=0)
    return response

@app.route('/showallcustomerorders', methods=['GET','POST'])
def showallcustomerorders():
    return render_template('showallcustomerorders.html', customerorders=session.query(CustomerOrder).all())

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)