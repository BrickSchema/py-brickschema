"""
Brickschema web module. This embeds a Flask webserver which provides a local web server with:
- SPARQL interpreter + query result visualization
- buttons to perform inference

TODO:
- implement https://www.w3.org/TR/sparql11-protocol/ on /query
"""
from flask import Flask, request, json, jsonify, redirect
from rdflib.plugins.sparql.results.jsonresults import JSONResultSerializer
import pkgutil
import io


class Server:
    def __init__(self, graph):
        self.graph = graph
        self.app = Flask(__name__, static_url_path="/static")

        self.app.route("/query", methods=["GET", "POST"])(self.query)
        self.app.route("/reason/<profile>", methods=["POST"])(self.apply_reasoning)
        self.app.route("/", methods=["GET"])(self.home)

    def query(self):
        if request.method == "GET":
            query = request.args.get("query")
        elif (
            request.method == "POST"
            and request.content_type == "application/x-www-form-urlencoded"
        ):
            query = request.form.get("query")
        elif (
            request.method == "POST"
            and request.content_type == "application/sparql-query"
        ):
            print("SPARQL", request.form.keys())
            query = request.get_data()
        print(query)
        results = self.graph.query(query)
        json_results = io.StringIO()
        JSONResultSerializer(results).serialize(json_results)
        return jsonify(json.loads(json_results.getvalue()))

    def home(self):
        return pkgutil.get_data(__name__, "web/index.html").decode()

    def apply_reasoning(self, profile):
        self.graph.expand(profile)
        return jsonify(len(self.graph))

    def start(self, address):
        assert len(address.split(":")) == 2
        host, port = address.split(":")
        self.app.run(host="localhost", port="8080")
