from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum, Enum
import os
from typing import Tuple, Iterable

from sqlalchemy import (
    extract, create_engine, select, asc, 
    String, Float, DateTime, Engine, func, text
)

from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
    sessionmaker, Session
)


#
#   DATABASE SCHEMA
#
class DatabaseClass(DeclarativeBase):
    pass

class ObservationRealtime(DatabaseClass):
    __tablename__ = "OBSERVATION_REALTIME"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    variable: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

class ObservationHourly(DatabaseClass):
    __tablename__ = "OBSERVATION_HOURLY"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    variable: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)


#
#   DATABASE UTIL
#
@dataclass
class DeleteOldestObservationHourlyResult:
    variable: str
    count: int

@dataclass
class AddDatabaseObservationResult:
    variable: str
    count: int = None
    averaged_value: bool = False
    average: float = None
    deleted_oldest: DeleteOldestObservationHourlyResult = None


class EObservationFrequency(Enum):
    Realtime = ObservationRealtime
    Hourly = ObservationHourly



class Database:
    def __init__(self, database_path: str, hourly_buffer_size: int=24*30*60):

        """
        refresh_rate: int
            how many observations per hour. default=2 observations per second
        """
        self.hourly_buffer_size = hourly_buffer_size
        self.database_path = database_path
        self.engine, self.session = Database.create_database(database_path)

    @staticmethod
    def create_database(database_path: str) -> Tuple[Engine,  Session]:
        engine = create_engine(f"sqlite:///{database_path}")
        Session = sessionmaker(bind=engine)
        DatabaseClass.metadata.create_all(bind=engine)
        return engine, Session()

    def _db_timestamp_current_hour(self):
        return func.strftime('%Y-%m-%d %H:00:00', func.now())

    def _db_timestamp_last_hour(self):
        return func.now()


    def add_observation(self, humidity: float, temperature: float) -> Iterable[AddDatabaseObservationResult]:
        results = []
        for variable, value in zip(["HUMIDITY", "TEMPERATURE"], [humidity, temperature]):
            current_hour_count = self.get_count_current_hour_observations(variable)

            result = AddDatabaseObservationResult(variable, current_hour_count)
            if current_hour_count == 0:
                result.averaged_value = True
                result.average = self.average_last_hour(variable)
            results.append(result)

            obs = ObservationRealtime(variable=variable, value=value)
            self.session.add(obs)
            self.session.commit()

            if not result.averaged_value:
                continue

            result.deleted_oldest = self.delete_oldest_hourly_observations(variable)

        return results


    def get_count_current_hour_observations(self, variable: str) -> int:
        return (self.session.query(ObservationRealtime)
                            .filter(
                                ObservationRealtime.date >= self._db_timestamp_current_hour(),
                                ObservationRealtime.variable == variable)
                            .count())

    def get_last_n_observations(self, variable: str, n: int, obs_type: EObservationFrequency = EObservationFrequency.Realtime) -> Iterable[ObservationRealtime]:
        obs_type = obs_type.value
        return (self.session.query(obs_type)
                    .filter(obs_type.variable == variable)
                    .order_by(obs_type.id.desc())
                    .limit(n))[::-1]


    def average_last_hour(self, variable: str):
        now = datetime.now()
        start_of_last_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        average = (self.session.query(func.avg(ObservationRealtime.value))
                            .filter(
                                ObservationRealtime.date >= start_of_last_hour,
                                ObservationRealtime.date < func.now(),
                                ObservationRealtime.variable == variable)
                            .scalar())
        if average is None:
            return None

        obs_hourly = ObservationHourly(
            variable=variable, 
            value=average, 
            date=start_of_last_hour
        )
        self.session.add(obs_hourly)
        self.session.commit()
        return average


    def delete_oldest_hourly_observations(self, variable: str):
        total_count = (self.session.query(ObservationHourly)
                                  .filter(ObservationHourly.variable == variable)
                                  .count())
        excess_count = total_count - self.hourly_buffer_size

        if excess_count <= 0:
            return None

        oldest_observations = (self.session.query(ObservationHourly)
                                            .filter(ObservationHourly.variable == variable)
                                            .order_by(asc(ObservationHourly.id))
                                            .limit(excess_count))

        for observation in oldest_observations:
            self.session.delete(observation)
        self.session.commit()

        return DeleteOldestObservationHourlyResult(variable, len(oldest_observations))

    def update_hourly_observations(self, variable):
        hours = [ d[0] for d in self.session.query(
            func.strftime('%Y-%m-%d %H:00:00', ObservationRealtime.date).label("date"),
        ).filter(ObservationRealtime.variable == variable).distinct("date").all() ]
        res = hours

        for hour in hours:
            n_hourly = (self.session.query(ObservationHourly.date)
                                    .filter(ObservationHourly.date == hour)
                                    .filter(ObservationHourly.date >= func.now() - timedelta(days=-1))
                                    .count())
            if n_hourly > 0:
                continue

            hour_average = (self.session.query(
                func.avg(ObservationRealtime.value)
            ).filter(func.strftime('%Y-%m-%d %H:00:00', ObservationRealtime.date) == hour)
             .filter(ObservationRealtime.variable == variable)
             .all())[0][0]

            observation = ObservationHourly(
                variable=variable, 
                value=hour_average, 
                date=datetime.strptime(hour, '%Y-%m-%d %H:00:00')
            )
            self.session.add(observation)

            res = hour_average
        self.session.commit()
        return res



                



                

            



