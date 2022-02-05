from flask import Flask, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS
from mpesa import *

app = Flask(__name__)

from configs.base_config import Development, Production, Staging
app.config.from_object(Development)

alvapi_key = "EZKBB11OQDGS3BGK"
scheduler = BackgroundScheduler(daemon=True)
db = SQLAlchemy(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})
class Forex(db.Model):
    __tablename__ = 'forex'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(80), nullable=False)
    data = db.Column(db.JSON, unique=True)
    created_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

class STKData(db.Model):
    __tablename__ = 'stkdata'

    id = db.Column(db.Integer, primary_key=True)
    merchant_request_id = db.Column(db.String(80), nullable=False)
    checkout_request_id = db.Column(db.String(80), nullable=False)
    response_code = db.Column(db.String(80), nullable=False)
    response_description = db.Column(db.String(80), nullable=False)
    customer_message = db.Column(db.String(80), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

@app.before_first_request
def create_tables():
    db.create_all()
    print("Tables created")


@app.route("/")
def index():
    return "This is a private API"

@app.route("/json/forex")
def forex_api():
    # Get from DB
    data_json = Forex.query.all()
    # return "This is the great Paul"
    import ast
    res = json.dumps([ast.literal_eval(d.data) for d in data_json])

    return res

# M-Pesa routes
@app.route("/stkpush", methods=['GET', 'POST'])
def stk_push():
    api_data = request.get_json(force=True)
    phone_number = api_data['phoneNumber']
    account_number = '25747'
    amount = api_data['amount']
    header = {'Authorization': 'Bearer %s' % authenticator()}
    url = base_url + 'mpesa/stkpush/v1/processrequest'
    body = {
        "BusinessShortCode": business_short_code,
        "Password": generate_password(),
        "Timestamp": get_timestamp(),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": business_short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://mydomain.com/pat",
        "AccountReference": account_number,
        "TransactionDesc": "Edwin is shouting at us"
    }

    r = requests.post(url, json=body, headers=header).json()

    # 1. store the response in the database, i.e. the merchant request and the checkout request (make a new model for these)
    stored_response_data = STKData(merchant_request_id = r['MerchantRequestID'], checkout_request_id = r['CheckoutRequestID'], response_code = r['ResponseCode'], response_description = r['ResponseDescription'], customer_message = r['CustomerMessage'])
    db.session.add(stored_response_data)
    db.session.commit()    
    
    return r

@app.route("/stkpush/checker", methods=['GET', 'POST'])
def stk_push_checker():
    # 2. Change the status code received in step 1
    pass

# for safaricom
@app.route("/stkpush/processor", methods=['GET', 'POST'])
def stk_push_processor():
    # 3. Check what the user has done. The client shall do a loop every 5 seconds with the checkout request and the merchant request.
    pass

def request_scheduler():
    # try:
    #     # Make a GET Request to Alphavantage
    #     r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=' + alvapi_key)

    #     # Store the data received
    #     data = r.text

    #     # find out the type of the data
    #     print(type(data))

    #     # Convert from string to a dictionary using json.loads()
    #     data_json = json.loads(data)

    #     # Find out type of data
    #     print("From scheduler:", type(data_json))

    #     data = Forex(symbol="IBM", data=json.loads(json.dumps(data_json)))
    #     db.session.add(data)
    #     db.session.commit()
    # # except Exception as e:
    #     print("Error in scheduler:", e)
    return "hi"

# Create the scheduler job
scheduler.add_job(request_scheduler, 'interval', minutes=0.25)

# start the scheduler
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)