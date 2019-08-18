import anosql
import tenacity
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
import json
import logging
import os
import json
from flask_restful import Resource
import psycopg2.extras
import psycopg2
import api

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
    Stats API
    """
    def __init__(self):
        self.connection = self._connect_db()
        self.queries = anosql.from_path(f"{api.ROOT_DIR}/sql/stats_contributions.sql", "psycopg2")

    @tenacity.retry(stop=tenacity.stop_after_delay(api.TENACITY_DELAY))
    def _connect_db(self):
        return psycopg2.connect(
        user=api.DB_USER,
        password=api.DB_PASSWORD,
        host=api.DB_HOST,
        port=api.DB_PORT,
        database=api.DB_DATABASE,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    def get(self):
        """
        Returns:
            The stats view [{"repository": "name", "date": "2016-03", "number_of_new_contributors": 4}, ...]
            If table don't exist or is empty send a message
        """
        results = {"message": "No results to display"}
        try:
            results_query = self.queries.select_stats_contributions(self.connection)
            if results_query:
                results = results_query
        except (psycopg2.errors.UndefinedTable, psycopg2.ProgrammingError) as e:
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

if __name__ == "__main__":  # pragma: no cover
    application = main()
    application.run(host="0.0.0.0", port=5000)
