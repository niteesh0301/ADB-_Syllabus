import datetime
import os
import re

import pymongo

from flask import Flask,render_template,request,redirect,session

from bson import ObjectId

from Mail import send_email

dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = dbConn["OnlineAuction"] #db name


#db collections
admin_col = my_db["admin"]
trader_col = my_db["trader"]
buyer_col = my_db["buyer"]
category_col = my_db["category"]
product_col = my_db["product"]
product_session_col = my_db["sessions"]
payment_col = my_db["payments"]
bid_col = my_db["bid"]





APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"


#Flask Server Creation

app = Flask(__name__)

app.secret_key="auction"

admin_count = admin_col.find_one({})

if admin_count == None:
    admin_col.insert_one({"userName":"admin","password":"admin"})


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/adminLogin")
def adminLogin():
    return render_template("adminLogin.html")

@app.route("/traderLogin")
def traderLogin():
    return render_template("traderLogin.html")

@app.route("/buyerLogin")
def buyerLogin():
    return render_template("buyerLogin.html")

@app.route("/adminLoginAction",methods=['post'])
def adminLoginAction():
    userName = request.form.get("userName")
    password = request.form.get("password")
    count = admin_col.count_documents({"userName":userName,"password":password})
    if count > 0:
        session['role'] = "admin"
        return redirect("/admin_home")
    else:
        return render_template("message.html",message="Invalid Login Details",color="text-danger")

@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/categories")
def categories():
    categories = category_col.find()
    return render_template("categories.html",categories=categories)

@app.route("/addCategoryAction")
def addCategoryAction():
    category_name  = request.args.get("category_name")
    query = {"category_name":category_name}
    count = category_col.count_documents(query)
    if count>0:
        return render_template("message.html",message="Category Exists",color="text-danger")
    else:
        category_col.insert_one(query)
        return redirect("/categories")


@app.route("/tReg")
def tReg():
    return render_template("tReg.html")

@app.route("/bReg")
def bReg():
    return render_template("bReg.html")


@app.route("/traderRegAction",methods=['post'])
def traderRegAction():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    address = request.form.get("address")
    city = request.form.get("city")
    zipCode = request.form.get("zipCode")
    query = {"$or":[{"email":email},{"phone":phone}]}
    count = trader_col.count_documents(query)
    if count ==0:
        trader_col.insert_one({"first_name":first_name,"last_name":last_name,"phone":phone,"password":password,"address":address,"email":email,"city":city,"zipCode":zipCode,"status":'Not Verified'})
        return render_template("message.html",message="Registered Successfully",color="text-success")
    else:
        return render_template("message.html", message="Duplicate Trader Details", color="text-danger")

@app.route("/buyerRegAction",methods=['post'])
def buyerRegAction():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    city = request.form.get("city")
    zipCode = request.form.get("zipCode")
    ssn = request.form.get("ssn")
    dob = request.form.get("dob")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    address = request.form.get("address")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = buyer_col.count_documents(query)
    if count == 0:
        buyer_col.insert_one({"first_name": first_name,"last_name":last_name, "city":city,"zipCode":zipCode,"ssn":ssn,"dob":dob,"phone": phone, "password": password, "address": address, "email": email})
        return render_template("message.html", message="Registered Successfully", color="text-success")
    else:
        return render_template("message.html", message="Duplicate Buyer Details", color="text-danger")

@app.route("/buyerLoginAction",methods=['post'])
def buyerLoginAction():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email,"password":password}
    count = buyer_col.count_documents(query)
    if count > 0:
        buyer = buyer_col.find_one(query)
        session['buyerId'] = str(buyer['_id'])
        session['role'] = 'buyer'
        return redirect("/buyerHome")
    else:
        return render_template("message.html", message="Invalid Buyer Details", color="text-danger")

@app.route("/traderLoginAction",methods=['post'])
def traderLoginAction():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email,"password":password}
    count = trader_col.count_documents(query)
    if count > 0:
        buyer = trader_col.find_one(query)
        if buyer['status']=='Verified':
            session['traderId'] = str(buyer['_id'])
            session['role'] = 'trader'
            return redirect("/traderHome")
        else:
            return render_template("message.html", message="You Can Login After  Admin Verification", color="text-primary")
    else:
        return render_template("message.html", message="Invalid Trader Details", color="text-danger")

@app.route("/buyerHome")
def buyerHome():
    buyer = buyer_col.find_one({'_id':ObjectId(session['buyerId'])})
    return render_template("buyerHome.html",buyer=buyer)

@app.route("/traderHome")
def traderHome():
    trader = trader_col.find_one({'_id': ObjectId(session['traderId'])})
    return render_template("traderHome.html",trader=trader)

@app.route("/products")
def products():
    query = {}
    if session['role'] == 'admin':
        query = {}
    elif session['role'] == 'trader':
        query = {"traderId":ObjectId(session['traderId'])}
    categories = category_col.find()
    products = product_col.find(query)
    return render_template("products.html",getTrader_by_id=getTrader_by_id,getCategory_by_id=getCategory_by_id,categories=categories,products=products,getProduct_session_by_id=getProduct_session_by_id)

@app.route("/products_sessions")
def products_sessions():
    product_sessions = product_session_col.find()
    return render_template("products_sessions.html",product_sessions=product_sessions,getProduct_by_id=getProduct_by_id,getCategory_by_id=getCategory_by_id,getTrader_by_id=getTrader_by_id)

@app.route("/addProductAction",methods=['post'])
def addProductAction():
    productName = request.form.get("productName")
    price = request.form.get("price")
    categoryId = request.form.get("categoryId")
    productPicture = request.files.get("productPicture")
    quantity  =request.form.get("quantity")
    condition = request.form.get("condition")
    about = request.form.get("about")
    path = APP_ROOT + "/product_image/" + productPicture.filename
    productPicture.save(path)
    product_count = product_col.count_documents({"productName":productName})

    if product_count >0:
        return render_template("message.html",message="Duplicate Product Added",color="text-danger")
    else:
        product = product_col.insert_one({"productName":productName,"price":price,"categoryId":ObjectId(categoryId),"productPicture":productPicture.filename,"about":about,"traderId":ObjectId(session['traderId']),"status":"Not Available","quantity":quantity,"condition":condition})
        # productId = product.inserted_id
        # product_session_col.insert_one({"sessionStartDate":sessionStartDate,"sessionEndDate":sessionEndDate,"productId":ObjectId(productId)})
        return redirect("/products")

def getProduct_session_by_id(productId):
    product_session = product_session_col.find_one({"productId":ObjectId(productId)})
    return product_session

def getCategory_by_id(categoryId):
    category = category_col.find_one({'_id':ObjectId(categoryId)})
    return category

def getTrader_by_id(traderId):
    trader = trader_col.find_one({"_id":ObjectId(traderId)})
    return trader


@app.route("/update_buyer_wallet")
def update_buyer_wallet():
    buyerId = request.args.get("buyerId")
    buyer = buyer_col.find_one({"_id":ObjectId(buyerId)})
    return render_template("update_buyer_wallet.html",buyer=buyer,buyerId=buyerId)

@app.route("/update_buyer_wallet1",methods=['post'])
def update_buyer_wallet1():
    buyerId = request.form.get("buyerId")
    wallet_amount = request.form.get("wallet_amount")
    print(wallet_amount)
    if wallet_amount == '':
        return redirect("/buyerHome")
    else:
        buyer = buyer_col.find_one({"_id":ObjectId(buyerId)})
        query = {"$set":{"wallet_amount":int(buyer['wallet_amount'])+int(wallet_amount)}}
        buyer_col.update_one({"_id":ObjectId(buyerId)},query)
        return redirect("/buyerHome")
    #


@app.route("/searchProducts")
def searchProducts():
    categoryId = request.args.get("categoryId")
    productName = request.args.get("productName")
    if productName is None:
        productName = ''
    if categoryId is None:
        categoryId = ''
    if categoryId == '':
        query = {"status":"Posted For Bid","productName":re.compile(".*" + productName + ".*", re.IGNORECASE)}
    else:
        query = {"status": "Posted For Bid", "productName":re.compile(".*" + productName + ".*", re.IGNORECASE),"categoryId":ObjectId(categoryId)}
    products = product_col.find(query)
    productIds = []
    for product in products:
        productIds.append(product['_id'])
    current_date = datetime.datetime.now()
    query2 = {"productId":{"$in":productIds}}
    product_sessions = product_session_col.find(query2)
    categories = category_col.find()
    return render_template("searchProducts.html",categories=categories,str=str,categoryId=categoryId,productName=productName,product_sessions=product_sessions,getProduct_by_id=getProduct_by_id,getTrader_by_id=getTrader_by_id,getCategory_by_id=getCategory_by_id, current_date=current_date)


def getProduct_by_id(productId):
    product = product_col.find_one({"_id":ObjectId(productId)})
    return product


@app.route("/productStatus")
def productStatus():
    productId = request.args.get("productId")
    return render_template("productStatus.html",productId=productId)


@app.route("/productStatus1",methods=['post'])
def productStatus1():
    productId = request.form.get("productId")
    sessionStartDate = request.form.get("sessionStartDate")
    sessionEndDate = request.form.get("sessionEndDate")
    sessionStartDate = datetime.datetime.strptime(sessionStartDate, "%Y-%m-%dT%H:%M")
    sessionEndDate = datetime.datetime.strptime(sessionEndDate, "%Y-%m-%dT%H:%M")
    product_session_col.insert_one({"productId":ObjectId(productId),"sessionEndDate":sessionEndDate,"sessionStartDate":sessionStartDate})
    product_col.update_one({"_id":ObjectId(productId)},{"$set":{"status":'Posted For Bid'}})
    return redirect("/products")


@app.route('/bidProduct',methods=['post'])
def bidProduct():
    bid_amount = request.form.get("bid_amount")
    product_session_id = request.form.get("product_session_id")
    date = datetime.datetime.now()
    status = 'Bidded'
    query = {"product_session_id":ObjectId(product_session_id),"buyerId":ObjectId(session['buyerId']),"status":status}
    count = bid_col.count_documents(query)
    if count == 0:
        bid_col.insert_one({"bid_amount":bid_amount,"product_session_id":ObjectId(product_session_id),"date":date,"status":status,"buyerId":ObjectId(session['buyerId'])})
        return render_template("message.html",message="Product Bidded",color='text-success')
    else:
        bid = bid_col.find_one(query)
        query2 = {"$set":{"bid_amount":bid_amount}}
        bid2 = bid_col.update_one({"_id":ObjectId(bid['_id'])},query2)
        return render_template("message.html", message="Bid Updated", color='text-success')

@app.route("/auctions")
def auctions():
    query = {}
    if session['role'] == 'buyer':
        query = {"buyerId":ObjectId(session['buyerId']),"$or":[{"status":'Bidded'},{"status":'Assigned'},{"status":'Amount Paid'},{"status":'Dispatched'},{"status":'Received'}]}
    elif session['role'] == 'trader':
        query = {"traderId":ObjectId(session['traderId'])}
        products = product_col.find(query)
        productIds = []
        for product in products:
            productIds.append(product['_id'])
        query = {"productId":{"$in":productIds}}
        product_sessions = product_session_col.find(query)
        product_sessionIds = []
        for product_session in product_sessions:
            product_sessionIds.append(product_session['_id'])
        query = {"product_session_id":{"$in":product_sessionIds},"$or":[{"status":'Bidded'},{"status":'Assigned'},{"status":'Amount Paid'},{"status":'Dispatched'},{"status":'Received'}]}
    elif session['role'] =='admin':
        query ={}
    product_auctions = bid_col.find(query)
    return render_template("auctions.html",get_admin_amount=get_admin_amount,int=int,get_max_amount=get_max_amount,get_buyer_by_id=get_buyer_by_id,product_auctions=product_auctions,getProduct_session_by_id2=getProduct_session_by_id2,getProduct_by_id=getProduct_by_id)


def get_admin_amount(bid_amount,admin_price):
    bid_amount = int(bid_amount)
    admin_price = int(admin_price)
    admin_amount = bid_amount*admin_price/100
    return admin_amount

def getProduct_session_by_id2(product_session_id):
    product_session = product_session_col.find_one({'_id':ObjectId(product_session_id)})
    return product_session


@app.route("/productBiddings")
def productBiddings():
    productId = request.args.get("productId")
    product_session = product_session_col.find_one({"productId":ObjectId(productId)})
    product_auctions = bid_col.find({"product_session_id":ObjectId(product_session['_id'])})
    product_auctions = list(product_auctions)
    return render_template("productBiddings.html",get_max_amount=get_max_amount,get_buyer_by_id=get_buyer_by_id,product_auctions=product_auctions,getProduct_session_by_id2=getProduct_session_by_id2,getProduct_by_id=getProduct_by_id)

def get_buyer_by_id(buyerId):
    buyer = buyer_col.find_one({'_id':ObjectId(buyerId)})
    return buyer

def get_max_amount(bidId,product_session_id):
    product_bidding = bid_col.find_one({"status":"Bidded","product_session_id":ObjectId(product_session_id)}, sort=[("bid_amount", pymongo.DESCENDING)])
    max_amount = int(product_bidding['bid_amount'])
    bid = bid_col.find_one({"_id":ObjectId(bidId),"status":"Bidded"})
    bid_amount = int(bid['bid_amount'])
    print(max_amount,bid_amount)
    if int(max_amount) == int(bid_amount):
        return True
    else:
        return False


@app.route("/assignProduct")
def assignProduct():
    bidId = request.args.get("bidId")
    product_session_id = request.args.get("product_session_id")
    product_session = product_session_col.find_one({"_id":ObjectId(product_session_id)})
    product = product_col.find_one({"_id":ObjectId(product_session['productId'])})
    query = {"$set":{"status":"Assigned"}}
    bid_col.update_one({"_id":ObjectId(bidId)},query)
    bid = bid_col.find_one({"_id":ObjectId(bidId)})
    query3 = {"product_session_id": ObjectId(product_session_id), "status": 'Bidded'}
    query4 = {"$set": {"status": 'Suspended'}}
    bid_col.update_many(query3,query4)
    buyerId = bid['buyerId']
    buyer = buyer_col.find_one({'_id':ObjectId(buyerId)})
    send_email("Product Assigned", "The Product "+product['productName']+" is Assigned To You",buyer['email'])
    return render_template("message.html",message="The Product Is Assigned To "+str(buyer['first_name'])+"",color="text-success")


@app.route("/payAmount")
def payAmount():
    bidId = request.args.get("bidId")
    productId = request.args.get("productId")
    bid = bid_col.find_one({"_id":ObjectId(bidId)})
    return render_template("payAmount.html",bid=bid,bidId=bidId,productId=productId)

@app.route("/payAmount1",methods=['post'])
def payAmount1():
    productId = request.form.get("productId")
    bidId = request.form.get("bidId")
    amount = request.form.get("amount")
    bid = bid_col.find_one({'_id':ObjectId(bidId)})
    buyerId = bid['buyerId']
    payment_col.insert_one({"paidFor":ObjectId(productId),"bidId":ObjectId(bidId),"amount":amount,"paidBy":ObjectId(buyerId),"date":datetime.datetime.now(),"status":'Amount Paid'})
    query = {"$set":{"status":'Amount Paid'}}
    bid_col.update_one({"_id":ObjectId(bidId)},query)
    return render_template("message.html",message="Amount Paid",color="text-primary")


@app.route("/dispatchProduct")
def dispatchProduct():
    bidId = request.args.get("bidId")
    bid = bid_col.find_one({"_id":ObjectId(bidId)})
    buyerId = bid['buyerId']
    buyer = buyer_col.find_one({"_id":ObjectId(buyerId)})
    productId = request.args.get("productId")
    query = {"$set":{"status":'Product Assigned'}}
    product_col.update_one({"_id":ObjectId(productId)},query)
    query2 = {"$set":{"status":"Dispatched"}}
    bid_col.update_one({"_id":ObjectId(bidId)},query2)
    return render_template("message.html",message="Product Dispatched To "+str(buyer['first_name'])+"",color="text-success")


@app.route("/makeAsReceived")
def makeAsReceived():
    bidId = request.args.get("bidId")
    query = {"$set":{"status":"Received"}}
    bid_col.update_one({"_id":ObjectId(bidId)},query)
    return render_template("message.html", message="Product Received", color="text-success")


@app.route("/viewPayments")
def viewPayments():
    bidId = request.args.get("bidId")
    payment = payment_col.find_one({"bidId":ObjectId(bidId)})
    return render_template("viewPayments.html",get_buyer_by_id2=get_buyer_by_id2,payment=payment,get_product_by_id=get_product_by_id,get_trader_by_product_id=get_trader_by_product_id)

def get_product_by_id(paidFor):
    product = product_col.find_one({"_id":ObjectId(paidFor)})
    return product
def get_trader_by_product_id(productId):
    product = product_col.find_one({"_id":ObjectId(productId)})
    trader = trader_col.find_one({'_id':ObjectId(product['traderId'])})
    return trader

def get_buyer_by_id2(paidBy):
    buyer = buyer_col.find_one({"_id":ObjectId(paidBy)})
    return buyer


@app.route("/approveProduct")
def approveProduct():
    productId = request.args.get("productId")
    admin_price = request.args.get("admin_price")
    query = {"$set":{"status":"Available","admin_price":admin_price}}
    product_col.update_one({"_id":ObjectId(productId)},query)
    return render_template("message.html",message="Product Approved",color="text-success")

@app.route("/suspendedBiddings")
def suspendedBiddings():
    query = {}
    if session['role'] == 'admin':
        query = {"status":"Suspended"}
    elif session['role'] =='buyer':
        query = {"status": "Suspended","buyerId":ObjectId(session['buyerId'])}
    elif session['role'] == 'trader':
        query = {"traderId": ObjectId(session['traderId'])}
        products = product_col.find(query)
        productIds = []
        for product in products:
            productIds.append(product['_id'])
        query = {"productId": {"$in": productIds}}
        product_sessions = product_session_col.find(query)
        product_sessionIds = []
        for product_session in product_sessions:
            product_sessionIds.append(product_session['_id'])
        query = {"product_session_id": {"$in": product_sessionIds},"status":"Suspended"}
    product_auctions = bid_col.find(query)
    return render_template("suspendedBiddings.html",product_auctions=product_auctions,get_buyer_by_id=get_buyer_by_id,getProduct_by_id=getProduct_by_id,getProduct_session_by_id2=getProduct_session_by_id2)


@app.route("/traders")
def traders():
    traders = trader_col.find()
    return render_template("traders.html",traders=traders)

@app.route("/trader_status")
def trader_status():
    traderId = request.args.get("traderId")
    trader = trader_col.find_one({"_id":ObjectId(traderId)})
    if trader['status'] =='Not Verified':
        trader_col.update_one({"_id":ObjectId(traderId)},{"$set":{"status":'Verified'}})
    else:
        trader_col.update_one({"_id": ObjectId(traderId)}, {"$set": {"status": 'Not Verified'}})
    return redirect("/traders")


@app.route("/get_date_diff")
def get_date_diff():
    sessionStartDate = request.args.get("sessionStartDate")
    sessionEndDate = request.args.get("sessionEndDate")
    sessionStartDate = datetime.datetime.strptime(sessionStartDate, "%Y-%m-%dT%H:%M")
    sessionEndDate = datetime.datetime.strptime(sessionEndDate, "%Y-%m-%dT%H:%M")
    diff = sessionEndDate - sessionStartDate
    days, seconds = diff.days, diff.seconds
    hours = days * 24 + seconds // 3600
    return {"hours": hours}

app.run(debug=True)
