from flask import Flask
from flask_restful import Api
from flask_cors import CORS
import json
import logging
import os
import json
from flask_restful import Resource
from psycopg2.extras import RealDictCursor
import psycopg2

logging.basicConfig(level=logging.DEBUG)

class Index(Resource):
    """
    Caeli API
    """

    def get(self):
        """
        Returns:
            str: Hello world for people calling the api
        """
        json = {"message": "Hello, this api exist to query data" " produced by Caeli"}
        return json, 200


class Stats(Resource):
    """
    Job Recommender API
    """

    def __init__(self):
        self.connection = connect_db()

    def get(self):
        """
        Returns:
            The stats view [{"repository": "name", "date": "2016-03", "number_of_new_contributors": 4}, ...]
            If table don't exist or is empty send a message
        """
        results = {"message": "No results to display"}
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                cursor.execute("SELECT * FROM stats_contributions")
                results_query = cursor.fetchall()
                self.connection.commit()
                if results_query:
                    results = results_query
            except (psycopg2.errors.UndefinedTable) as e:
                logging.exception(e)
        return results, 200


def create_app():
    """
    Create the app and setting all the road here
    Returns:
        Flask: Flask application for the api
    """

    application = Flask(__name__)
    # bugsnag integration
    CORS(application)

    application.config["JSON_AS_ASCII"] = False
    application.config["DEBUG"] = True
    api = Api(application)
    # default index
    api.add_resource(Index, "/")
    api.add_resource(Stats, "/stats")
    return application


def main():
    application = create_app()
    return application


def connect_db():
    return psycopg2.connect(
        user=os.environ.get("POSTGRES_USER", "NOT_SET"),
        password=os.environ.get("POSTGRES_PASSWORD", "NOT_SET"),
        host=os.environ.get("POSTGRES_HOST", "NOT_SET"),
        port=os.environ.get("POSTGRES_PORT", "NOT_SET"),
        database=os.environ.get("POSTGRES_DB", "NOT_SET"),
    )


if __name__ == "__main__":  # pragma: no cover
    application = main()
    application.run(host="0.0.0.0", port=5000)
