from spacy import displacy
from flask import request, render_template, jsonify
import spacy
from app.services.graph import get_graph, get_graph_v2
from app.services.tagging import get_basic_info, get_wikidata_info
from nlp.feature_extractor import FeatureExtractor


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

    @app.route("/histogram/sentiment", methods=["GET"])
    def sentiment_histogram():
        pass

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

    @app.route("/histogram/co-occurrence", methods=["GET"])
    def co_occurrence_histogram():
        wiki_id = request.args.get("id")

        if wiki_id is None or not wiki_id.isdigit():
            return jsonify({"error": "Invalid ID"}), 400

        wiki_id = int(wiki_id)

        feature_extractor = FeatureExtractor(wiki_id)
        response, main_entity = (
            feature_extractor.create_extracted_features_json_wo_relatedness()
        )

        return (
            jsonify(
                {
                    "data": response,
                    "main_entity": main_entity,
                }
            ),
            200,
        )
    
    # Route for most occurred entities with page_number
    @app.route("/most-occurred-entities", methods=["GET"])
    def most_occurred_entities():
        wiki_id = request.args.get("id")
        wiki_id = int(wiki_id)
        page_number = request.args.get("page_number", 1)
        
        if page_number is None:
            return jsonify({"error": "Invalid page number"}), 400
        


        feature_extractor = FeatureExtractor(wiki_id)
        most_occurred_entities, max_page = (
            feature_extractor.get_most_occurred_entities(page_number)
        )

        return (
            jsonify(
                {
                    "most_occurred_entities": most_occurred_entities,
                    "max_page": max_page
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
