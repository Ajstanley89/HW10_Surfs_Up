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
        f'<H1>Avaliable Routes:</H1><br/>'
        f'<br/>'
        f'<u>Precipitation Data:</u><br/>'
        f'/api/v1.0/precipitation<br/>'
        f'<br/>'
        f'<u>Station List:</u><br/>'
        f'/api/v1.0/stations<br/>'
        f'<br/>'
        f'<u>Temperature Observation Data:</u><br/>'
        f'/api/v1.0/tobs<br/>'
        f'<br/>'
        f'<u>Tmin, Tavg, Tmax from Start Date (%Y-%m-%d):</u><br/>'
        f'/api/v1.0/2016-08-23<br/>'
        f'<br/>'
        f'<u>Tmin, Tavg, Tmax from Start Date and End Date (%Y-%m-%d):</u><br/>'
        f'/api/v1.0/2016-08-23/2016-09-23<br/>'
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
    # Find last Date
    max_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Convert max_date to date time
    last_dt = dt.datetime.strptime(max_date, '%Y-%m-%d')

    year_ago = last_dt - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.tobs).filter(func.strftime('%Y-%m-%d', Measurement.date) >= year_ago).all()

    last_year_tobs = []

    for date, tobs in results:
        tobs_dct = {}
        tobs_dct[date] = tobs
        last_year_tobs.append(tobs_dct)

    return jsonify(last_year_tobs)

# Define function to calculate Tmin, Tmax, Tavg
def temp_dates(start, end=None):
    '''
    Takes a start date and an optional end date in "%Y-%m-%d" format.

    Takes the given dates, and calculates the Tmin, Tavg, and Tmax wiithin the date range from the Hawaii.sqlliite database.

    Returns a dictionary containing the calculated temperature values.
    '''
    # Convert start date string to datetime
    start_dt = dt.datetime.strptime(start, '%Y-%m-%d')

    # Convert end date to datetime if not None
    if end != None:
        end_dt = dt.datetime.strptime(end, '%Y-%m-%d')

    # Define selection
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    # Query within date range. If there's an end date, use it
    if end != None:
        results = session.query(*sel).filter(func.strftime('%Y-%m-%d', Measurement.date) >= start_dt).filter(func.strftime(Measurement.date) <= end_dt).all()
    # If no end date, just use start date
    else:
        results = session.query(*sel).filter(func.strftime('%Y-%m-%d', Measurement.date) >= start_dt).all()
        
     # convert results to list
    temperatures = list(np.ravel(results))

    # Define keys for JSON dictionary
    temp_keys = ['Tmin','Tavg','Tmax']

    # Create a dictionary using the keys and the temperatures data

    temp_dict = dict(zip(temp_keys, temperatures))

    return temp_dict

@app.route('/api/v1.0/<start>')
def tobs_start(start):
    '''
    When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
    '''
    # Find Last date
    max_date = session.query(func.max(Measurement.date)).scalar()

    # Check if date is after the latest date in DB; if it is, return an error
    if start > max_date:
        return jsonify({"error": f"{start} out of range"}), 404

    # Call temp dates function to get temp dict. Return error message if date is in wrong format.
    try:
        temp_data = temp_dates(start)
    except ValueError:
                return jsonify({"error": f"{start} does not match format '%Y-%m-%d'"}), 404

    return jsonify(temp_data)

@app.route('/api/v1.0/<start>/<end>')
def tobs_start_end(start, end):
    '''
    When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.
    '''
    # Find last Date
    max_date = session.query(func.max(Measurement.date)).scalar()

    # Find First Date
    min_date = session.query(func.min(Measurement.date)).scalar()
    
    # Check if start date is after the latest date in DB; if it is, return an error
    if start > max_date:
        return jsonify({"error": f"{start} out of range"}), 404

    # Check if end date is before the earlist date in DB; if it is, return an error
    if end < min_date:
        return jsonify({"error": f"{end} out of range"}), 404

    # Call temp dates function to get temp dict. Return error message if date is in wrong format.
    try:
        temp_data = temp_dates(start, end)
    except ValueError:
                return jsonify({"error": f"Start or End date do not match format '%Y-%m-%d'"}), 404

    return jsonify(temp_data)


if __name__ == '__main__':
    app.run(debug=True)



