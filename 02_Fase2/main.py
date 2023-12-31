"""
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  +                                                                                                                      +   
  +  Project for the Astro Pi Competition                                                                                +
  +                                                                                                                      +
  +  This has been written by Pesulins team for the Astro Pi competition, 2023.                                    +
  +  This program is designed to photograph the Earth from in the Interntional Space Station                             +
  +  to process the images and analyze in NDVI index and study the health of the plants.                                 +
  +                                                                                                                      +
  +                                                                                                                      +
  +  Date   : 08/02/2023                                                                                                 +
  +                                                                                                                      +
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
"""

# Import different libraries
from pathlib import Path
from logzero import logger, logfile        # logging info, errors and warning
from sense_hat import SenseHat             # librarie sense hat
from picamera import PiCamera              # camera librarie
from orbit import ISS
from datetime import datetime, timedelta   # generate date and time
from time import sleep                     # can make pauses
import random                              # random processes
import os                                  # generate path file
import csv                                 # generate csv file
import reverse_geocoder as rg              # can determine country, city and village
from time import sleep




def create_csv_file(data_file):
    "Create a new CSV file and add the header row"
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Date/time","Num Foto","Temperature", "Humidity","Pressure","Pitch","Roll","Yaw","Compass N:","Latitude","Longitude","Reverse-geocoder")
        writer.writerow(header)

def add_csv_data(data_file, data):
    """Add a row of data to the data_file CSV"""
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)
        
def convert(angle):
    """
    Convert a `skyfield` Angle to an EXIF-appropriate
    representation (rationals)
    e.g. 98° 34' 58.7 to "98/1,34/1,587/10"

    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    
     Convierta un ángulo `skyfield` en un EXIF apropiado
     representación (racionales)
     p.ej. 98° 34' 58,7 a "98/1,34/1587/10"

     Devuelve una tupla que contiene un valor booleano y el ángulo convertido,
     con el booleano indicando si el ángulo es negativo.
     """
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def capture(camera, image):
    """Use `camera` to capture an `image` file with lat/long EXIF data."""
    location = ISS.coordinates()

    # Convert the latitude and longitude to EXIF-appropriate representations
    south, exif_latitude = convert(location.latitude)
    west, exif_longitude = convert(location.longitude)

    # Set the EXIF tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # Capture the image
    camera.capture(image)


base_folder = Path(__file__).parent.resolve()

# Set a logfile name
logfile(base_folder/"events.log")

# Set up Sense Hat
sense = SenseHat()

# Set up camera
cam = PiCamera()
cam.resolution = (2592, 1944)

# Initialise the CSV file
data_file = base_folder/"data/data.csv"
create_csv_file(data_file)

# Initialise the photo counter
counter = 1
# Record the start and current time
start_time = datetime.now()
now_time = datetime.now()
# Run a loop for (almost) three hours
while (now_time < start_time + timedelta(minutes=178)):
    try:
        humidity = round(sense.humidity, 4)
        temperature = round(sense.temperature, 4)
        pressure = round(sense.pressure, 4)
        # Get coordinates of location on Earth below the ISS
        location = ISS.coordinates()
        o = sense.get_orientation()        
        pitch,roll,yaw = round(o["pitch"],3),round(o["roll"],3),round(o["yaw"],3)
         #compass N:
        north = sense.get_compass()
        
        # Save the data to the file
        data = (
            datetime.now(),
            counter,
            humidity,
            temperature,
            pressure,
            pitch,roll,yaw,north,
            location.latitude.degrees,
            location.longitude.degrees,
            location
            
            
        )
        add_csv_data(data_file, data)
        # Capture image
        image_file = f"{base_folder}/images/photo_{counter:03d}.jpg"
        capture(cam, image_file)
        # Log event
        logger.info(f"iteration {counter}")
        counter += 1
        sleep(15)
        # Update the current time
        now_time = datetime.now()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}')
  