from .cassandra_provider import cassandra_session
from .guts import retrieve_all_lwts
from .options import options


def main():
    with cassandra_session() as session:
        rows = retrieve_all_lwts(session)
        print('done.')
