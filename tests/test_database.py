import pytest

from src.server.database import DatabaseClass, ObservationRealtime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)

@pytest.fixture(scope='module')
def setup_module():
    DatabaseClass.metadata.create_all(engine)

def test_creating_database(setup_module):
    session = Session()

    observation = ObservationRealtime(
        variable="HUMIDITY",
        value=1.0
    )

    session.add(observation)
    session.commit()

    db_obs = session.get(ObservationRealtime, observation.id)
    assert db_obs is not None
    assert db_obs.value == 1.0
    assert db_obs.date is not None

