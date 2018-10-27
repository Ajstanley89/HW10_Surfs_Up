# Import Flask
from flask import Flask, jsonify

import numpy as np 

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct

import datetime as dt
from datetime import datetime

# Setup Database Stuff Here
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect existing db into new model
Base = automap_base()
# reflect tables
Base.prepare(engine, reflect=True)

# Save references to tables

Measurement = Base.classes.measurement
Station = Base.classes.station

# Create session to link Python to the DB
session = Session(engine)

#################################################
# Flask Routes
#################################################

# Flask setup
app = Flask(__name__)

# Define what happens when user hits the index rout
@app.route("/")
def home():
    '''List all available api routes here'''
    return(
        f'Avaliable Routes: <br/>'
        f'/api/v1.0/precipitation<br/>'
        f'/api/v1.0/stations<br/>'
        f'/api/v1.0/tobs<br/>'
    )

@app.route('/api/v1.0/precipitation')
def precipitation():
    '''
    Convert the query results to a Dictionary using `date` as the key and `tobs` (I think this is a typo. Should be 'prcp') as the value.
    
    Return the JSON representation of your dictionary.
    '''

    # Query date and precipitation data
    results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date.desc()).all()

    # Create List of dictionaries using date as key and prcp as the value
    date_prcp = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict[date] = prcp
        date_prcp.append(prcp_dict)

    return jsonify(date_prcp)

@app.route('/api/v1.0/stations')
def stations():
    '''
    Return a JSON list of stations from the dataset.
    '''
    # Query Stations
    results = session.query(Station.name).all()

    # Convert to normal list
    station_names = list(np.ravel(results))

    return jsonify(station_names)

@app.route('/api/v1.0/tobs')
def tobs():
    '''
    Query for the dates and temperature observations from a year from the last data point.

    Return a JSON list of Temperature Observations (tobs) for the previous year.
    '''
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')

    year_ago = last_date - dt.timedelta(days=365)

    last_year_tobs = session.query(Measurement.date, Measurement.tobs).\
                    filter(func.strftime('%Y-%m-%d', Measurement.date) >= year_ago).all()

    return jsonify(last_year_tobs)

if __name__ == '__main__':
    app.run(debug=True)



