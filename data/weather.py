import debug
import time
import pyowm
from pyowm.commons.exceptions import APIResponseError
from pyowm.commons.exceptions import APIRequestError

WEATHER_UPDATE_RATE = 10 * 60 # 10 minutes between weather updates

class Weather:

  def __init__(self, apikey, location, metric):
    self.apikey = apikey
    self.location = location
    self.metric = metric
    self.temperature_unit = "celsius" if metric else "fahrenheit"
    self.speed_unit = "meters_sec" if metric else "miles_hour"
    self.starttime = time.time()
    self.client = pyowm.OWM(self.apikey)
    self.mgr = self.client.weather_manager()

    self.temp       = None
    self.wind_speed = None
    self.wind_dir   = None
    self.conditions = None
    self.icon_name  = None

    # Remember if the API key was invalid so we don't keep trying to make calls with it
    self.apikey_valid = True

    # Force an update for our initial data
    self.update(True)

  # Return true if we have valid weather data available.
  # If we have a valid temp, we should be able to assume wind/conditions also exist
  def available(self):
    return self.temp != None

  # Make a call to the open weather maps API and update our instance variables
  # Pass True if you need to ignore the update rate (like for our first update)
  def update(self, force=False):
    if force == True or self.__should_update():
      debug.log("Weather should update!")
      self.starttime = time.time()
      if self.apikey_valid:
        debug.log("API Key hasn't been flagged as bad yet")
        try:
          self.observation = self.mgr.weather_at_place(self.location)
          weather = self.observation.weather
          self.temp = weather.temperature(self.temperature_unit).get('temp', -99)
          self.wind_speed = weather.wind(self.speed_unit).get('speed', -9)
          self.wind_dir = weather.wind(self.speed_unit).get('deg', 0)
          self.conditions = weather.status
          self.icon_name = weather.weather_icon_name
          debug.log("Weather: {}; Wind: {}; {} ({})".format(self.temperature_string(), self.wind_string(), self.conditions, self.icon_filename()))
        except APIResponseError:
          debug.warning("[WEATHER] The API key provided doesn't appear to be valid. Please check your config.json.")
          debug.warning("[WEATHER] You can get a free API key by visiting https://home.openweathermap.org/users/sign_up")
          self.apikey_valid = False
        except APIRequestError as e:
          debug.warning("[WEATHER] Fetching weather information failed from a connection issue.")
          debug.log("[WEATHER] Error Message: {}".format(e))
          # Set some placeholder weather info if this is our first weather update
          if self.temp is None:
            self.temp = -99
          if self.wind_speed is None:
            self.wind_speed = -9
          if self.wind_dir is None:
            self.wind_dir = 0
          if self.conditions is None:
            self.conditions = "Error"
          if self.icon_name is None:
            self.icon_name = "50d"

  def temperature_string(self):
    return "{}{}".format(int(round(self.temp)), self.temperature_unit[:1].upper())

  def wind_speed_string(self):
    speed_unit_string = "m/s" if self.speed_unit == 'meters_sec' else 'mph'
    return "{}{}".format(int(round(self.wind_speed)), speed_unit_string)

  def wind_dir_string(self):
    return self.__deg_to_compass(self.wind_dir)

  def wind_string(self):
    return "{} {}".format(self.wind_speed_string(), self.wind_dir_string())

  def icon_filename(self):
    return "Assets/weather/{}.png".format(self.icon_name)

  def __should_update(self):
    endtime = time.time()
    time_delta = endtime - self.starttime
    return time_delta >= WEATHER_UPDATE_RATE

  def __deg_to_compass(self, degrees):
    val = int((degrees/22.5) + 0.5)
    arr = ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return arr[(val % 16)]
