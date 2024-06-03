from spacy import displacy
from flask import request, render_template, jsonify
import spacy
from app.services.graph import get_graph, get_graph_v2
from app.services.tagging import get_basic_info, get_wikidata_info
from nlp.feature_extractor import FeatureExtractor
from nlp.otf_feature_extractor import OTFFeatureExtractor


def init_routes(app, db, cache):
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/search/", methods=["GET"])
    def search():
        query = request.args.get("q", "").strip()

        if query.strip() == "":
            return jsonify({"error": "Empty query"}), 204

        try :
            if request.headers.getlist("X-Forwarded-For"):
                ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                ip = request.remote_addr
        except:
            ip = "127.0.0.1"

        return jsonify(get_basic_info(query, ip, db)), 200


    @app.route("/graph", methods=["GET"])
    def graph():
        wiki_id = request.args.get("id")

        if wiki_id is None:
            return jsonify({"error": "Invalid ID"}), 400

        if not wiki_id.isdigit():
            return jsonify({"error": "Invalid ID"}), 400

        wiki_id = int(wiki_id)

        return jsonify(get_graph_v2(wiki_id, db, cache)), 200

    @app.route("/wiki-info", methods=["GET"])
    def wiki_info():
        wiki_id = request.args.get("id")

        if wiki_id is None:
            return jsonify({"error": "Invalid ID"}), 400

        wiki_id = str(wiki_id)

        return jsonify(get_wikidata_info(wiki_id)), 200

    @app.route("/general-info", methods=["GET"])
    def general_info():
        wiki_id = request.args.get("id")

        if wiki_id is None or not wiki_id.isdigit():
            return jsonify({"error": "Invalid ID"}), 400

        wiki_id = int(wiki_id)

        feature_extractor = OTFFeatureExtractor(wiki_id, db)
        response, most_occurred_entities, main_entity = feature_extractor.prepare_result()

        return (
            jsonify(
                {
                    "data": response,
                    "most_occurred_entities": most_occurred_entities,
                    "main_entity": main_entity,
                }
            ),
            200,
        )

    @app.route("/part-of-speech", methods=["GET"])
    def part_of_speech():
        query = request.args.get("q", "").strip()

        if query.strip() == "":
            return jsonify({"error": "Empty query"}), 204

        nlp = spacy.load("en_core_web_sm")
        rendered = displacy.render(nlp(query), style="dep")

        return rendered, 200
