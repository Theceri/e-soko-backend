from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests,json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS

app = Flask(__name__)
alvapi_key = "EZKBB11OQDGS3BGK"
scheduler = BackgroundScheduler(daemon=True)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///alphavantage.db"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/alphavantage"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})

class Forex(db.Model):
    __tablename__ = 'forex'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(80), nullable=False)
    data = db.Column(db.JSON, unique=True)
    created_date  = db.Column(db.DateTime, nullable=False, server_default=func.now())
    
@app.before_first_request
def create_tables():
    db.create_all()
    print("Tables created")

@app.route("/")
def index():
   return "This is a private API"

@app.route("/json/forex")
def forex_api():
    #Get from DB
    data_json=Forex.query.all()
    import ast
    res =json.dumps([ast.literal_eval(d.data) for d in data_json])
    return res    
 
def request_scheduler():
    # try:
        # Make a GET Request to Alphavantage
        r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=' + alvapi_key)

        #Store the data received
        data = r.text

        # find out the type of the data
        print(type(data))

        #Convert from string to a dictionary using json.loads()
        data_json = json.loads(data)

        #Find out type of data
        print("From scheduler:",type(data_json))

        data = Forex(symbol="IBM", data=json.loads(json.dumps(data_json)))
        db.session.add(data)
        db.session.commit()
    # except Exception as e:
    #     print("Error in scheduler:", e)

#Create the scheduler job
scheduler.add_job(request_scheduler, 'interval', minutes=0.25)

#start the scheduler
scheduler.start()    

if __name__ == "__main__":
    app.run()