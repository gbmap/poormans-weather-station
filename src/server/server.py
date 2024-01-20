import serial
from loguru import logger

import src.server.database as db

def start_database() -> db.Database:
    db_path = "database.db"
    logger.info(f"No database instance, creating. [PATH: {db_path}]")
    return db.Database(db_path, 30*60)

def main():
    try:
        database = start_database()
    except Exception as e:
        logger.critical(f"Failed to create database: {e}")

    bt_port, baud_rate = 'COM6', 9600
    logger.info(f"Starting bluetooth. [PORT: {bt_port}] [BAUD RATE: {baud_rate}]")
    try:
        bluetooth = serial.Serial(bt_port, baud_rate)
    except Exception as e:
        logger.critical(f"Failed to start bluetooth: {e}")
        return

    while True:
        try:
            data = bluetooth.readline().decode('utf-8').replace("\r\n", "")
            hum, tem = map(lambda s: float(s.split(":")[-1]), list(data.split(";")))

            logger.info(f"[HUMIDITY: {hum}][TEMPERATURE: {tem}]")
            results = database.add_observation(hum, tem)
            for result in results:
                if result.averaged_value and result.average:
                    logger.info(f"Averaged hourly. [VARIABLE: {result.variable}] [VALUE: {result.averaged_value}]")
                    if result.deleted_oldest:
                        logger.warning(f"Cleared oldest observations. [VARIABLE: {result.deleted_oldest.variable}] [COUNT: {result.deleted_oldest.count}]")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()