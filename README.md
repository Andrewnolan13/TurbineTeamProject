# TurbineTeamProject

Goal: Predict (power output/something else?) for wind turbines using weather forcast. Can be used to schedule maintenance. 

How: Get [historical weather data](https://open-meteo.com/). Get Wind turbine data (perferably for Ireland, perferably for more than one location). Train a model.

Deploy: make nice frontend with Dash. Use weather forecast api's for realtime updates. 

Problems: What does the weather data need to have? what does the wind turbine data need to have? Not sure because don't have wind turbine data yet.  



Goal: Dashboard and realtime prediction for different locations:

On-shore : 
Off-shore :


GEt weather data for JAN FEB 2021, (Windspeed, and any other if possible)

Week After: Atmospheric pressure, Hubheight for prediction

How to run:
1. clone the repo
2. cd to the TurbineTeamProject repo
3. run
   ```bash
   python -m src
   ```
4. NB if it's your first time to run the dashboard, you will need to create and fill up the database or else the dashboard will be painfully slow on first run. In order to do that, run the following command
   ```bash
   python first_run.py
   ``` 
