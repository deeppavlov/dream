import pytest
import poller
from multiprocessing import Process

@pytest.fixture(scope="session", autouse=True)
def pol():
    p = Process(target=poller.main, kwargs={'model_url': 'http://0.0.0.0:5000/answer'})
    p.start()
    yield
    p.terminate()
    p.join()
