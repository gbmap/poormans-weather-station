
# src/

## arduino/

### pmws.ino
Arduino code for reading DHT11 temp and humidity, printing to LCD screen and sending data through bluetooth.

## server/

### server.py
Reads bluetooth data from serial port COM4 and adds observations to the database.

### database.py
Data model and database utilities.

## dashboard/

### main.py
Dash panel with graphs.