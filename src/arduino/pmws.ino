#include "DHT.h"
#include <SoftwareSerial.h>
#include <LiquidCrystal.h>

#define DHT11_PIN 7

DHT dht11(DHT11_PIN, DHT11);

//                                RS, E, D4, D5, D6, D7
LiquidCrystal lcd = LiquidCrystal(13, 12, 11, 10, 9, 8);

String screenRow0;
String screenRow1;

void setup() {
  Serial.begin(9600);
  lcd.begin(16,2);
  dht11.begin();
}

void printStatus(float humidity, float temperature) {
  lcd.clear();
  lcd.setCursor(2, 0);

  screenRow0 = "TEMP: " + String(temperature) + "C";
  lcd.print(screenRow0);

  screenRow1 = "HUMI: " + String(humidity) + "%";
  lcd.setCursor(2, 1);
  lcd.print(screenRow1);
}


void loop() {
  // wait a few seconds between measurements.
  delay(2000);

  float humi  = dht11.readHumidity();
  float tempC = dht11.readTemperature();

  // check if any reads failed
  if (isnan(humi) || isnan(tempC)) {
    Serial.println("Failed to read from DHT11 sensor!");
  } else {
    Serial.print("H:");
    Serial.print(humi);
    Serial.print(";");
    Serial.print("T:");
    Serial.println(tempC);
  }

  printStatus(humi, tempC);
}