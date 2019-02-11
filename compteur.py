#!/usr/bin/python3.6
# -*-coding:UTF-8-*#

#----------------------------------------------------------------------
#  (c) David ROUBLOT, 2019
#----------------------------------------------------------------------

#----------------------------------------------------------------------
#IMPORTING
#----------------------------------------------------------------------
import requests
from flask import Flask, request, redirect, url_for, render_template
from waitress import serve
import configparser
from time import sleep

from datetime import datetime
import babel
from babel.dates import format_date, format_datetime, format_time

import threading


#  FLASK CONFIG
WEBSITE_ADDRESS = 'http://stalagtic-dev.ovh/cvs'

# Flask env
app = Flask(__name__)
app.debug= True
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config.from_object(__name__)
app.config['WEBSITE_ADDRESS'] =  WEBSITE_ADDRESS
app.secret_key = ''

#----------------------------------------------------------------------
#  GLOBALS
#----------------------------------------------------------------------
#  we have to load this from config file, but ...

Sites = [{"ID" : ,
            "Name" : "CVS Marie Thal-Marmoutier",
            "API": ""
            },
            {"ID" : ,
            "Name" : "École du Bouc d’Or",
            "API": ""
            },
            {"ID" : ,
            "Name" : "Ecole de Dossenheim",
            "API": ""
            },
            {"ID" : ,
            "Name" : "Club House Saverne",
            "API": ""
            }
            ]

Update = format_datetime(datetime.now(), "dd MMMM YYYY kk:mm", locale='fr')

#----------------------------------------------------------------------
#  GETTING DATAS EVERY 15MINS
#----------------------------------------------------------------------
# simple function started as thread

semaphore_RefreshData = threading.Event()
def RefreshData():
    global Update, Sites
    error = False

    while not semaphore_RefreshData.isSet():

        for site in Sites:
            # requesting total prod
            r = requests.get(f"https://monitoringapi.solaredge.com/site/"
                             f"{site['ID']}/overview?api_key={site['API']}")
            if r.status_code == 200:
                JSONResult = r.json()
                site["lifetimeproduction"] = int(JSONResult["overview"]["lifeTimeData"]["energy"]) / 1000
            else:
                error = True

            # requesting additional envBenefits
            r = requests.get(f"https://monitoringapi.solaredge.com/site/"
                             f"{site['ID']}/envBenefits?systemUnits=Metrics&api_key={site['API']}")
            if r.status_code == 200:
                JSONResult = r.json()
                site["trees"] = JSONResult["envBenefits"]["treesPlanted"]
                site["lightbulbs"] = JSONResult["envBenefits"]["lightBulbs"]
                site["CO2"] = JSONResult["envBenefits"]["gasEmissionSaved"]["co2"]
            else:
                error = True

        if not error is True:
            Update = format_datetime(datetime.now(), "d MMMM YYYY H'h'mm", locale='fr')

        sleep(900)

TaskerThread = threading.Thread(name="RefreshData", target=RefreshData)
TaskerThread.start()

#----------------------------------------------------------------------
# FLASK ROUTES                                                        #
#----------------------------------------------------------------------

@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():
    # 1 calculate the values to display
    Sites_Prod = '{:.2f}'.format(sum(item['lifetimeproduction'] for item in Sites))
    Sites_CO2 = '{:.2f}'.format(sum(item['CO2'] for item in Sites))
    Sites_Trees = '{:.1f}'.format(sum(item['trees'] for item in Sites))
    Sites_Bulbs = '{:.2f}'.format(sum(item['lightbulbs'] for item in Sites))
    Home_Use =  '{:.1f}'.format(float(Sites_Prod) / 2700)
    Car_Power = '{:.1f}'.format(float(Sites_Prod) / 18 * 100)
    Car_Planet = '{:.2f}'.format((float(Sites_Prod) / 20.3 * 100) / 40075)
    #  we also send the Sites dic to Flask

    return render_template('index.html',
                           Sites_Prod = Sites_Prod,
                           Sites_CO2 = Sites_CO2,
                           Sites_Trees = Sites_Trees,
                           Sites_Bulbs = Sites_Bulbs,
                           Home_Use = Home_Use,
                           Car_Power = Car_Power,
                           Car_Planet = Car_Planet,
                           Update = Update,
                           Sites = Sites)


#----------------------------------------------------------------------
# STARTING                                                            #
#----------------------------------------------------------------------

if __name__ == "__main__":
    print("starting ... Compteur Centrales Villageoises")
    import os
    if 'WINGDB_ACTIVE' in os.environ:
        app.debug = False
        app.run(host="0.0.0.0", port=5000)
    else:
        serve(app,  trusted_proxy = True, host='0.0.0.0', port='5005')
