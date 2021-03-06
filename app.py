import json
import os
from db import Entry, Cat
from json import dumps
from db import db
from flask import Flask, Response
from flask import request
from email_sender import send_email
import random


from flask_cors import CORS

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
db_filename = "cats.db"


# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True

# POSTGRES = {
#     "user": os.environ["POSTGRES_USER"],
#     "pw": os.environ["POSTGRES_PASSWORD"],
#     "db": os.environ["POSTGRES_DATABASE"],
#     "host": os.environ["POSTGRES_HOST"],
#     "port": os.environ["POSTGRES_PORT"],
# }
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "postgresql://%(user)s:\%(pw)s@%(host)s:%(port)s/%(db)s" % POSTGRES
# )

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)
with app.app_context():
    db.create_all()

# generalized response formats
def success_response(data, code=200):
    return Response(dumps({"success": True, "data": data}), mimetype="text/json")


def failure_response(message, code=404):
    return Response(dumps({"success": False, "error": message}), mimetype="text/json")


# @cross_origin(origin="*", headers=["access-control-allow-origin", "Content-Type"])
@app.route("/")
def hello_world():
    return success_response("This works!")


@app.route("/api/entries/")
def get_entries():
    return success_response([e.serialize() for e in Entry.query.all()])


@app.route("/api/profiles/")
def get_profiles():
    return success_response([c.serialize() for c in Cat.query.all()])


@app.route("/api/profiles/<int:profile_id>/")
def get_profile(profile_id):
    cat = Cat.query.filter_by(id=profile_id).first()
    if cat is None:
        return failure_response(f"No profile found for cat with id {profile_id}.")
    return success_response(cat.serialize())


@app.route("/api/profiles/<int:profile_id>/", methods=["DELETE"])
def delete_profile(profile_id):
    cat = Cat.query.filter_by(id=profile_id).first()
    db.session.delete(cat)
    db.session.commit()
    return success_response("Deleted!")


@app.route("/api/entries/<int:entry_id>/", methods=["DELETE"])
def delete_entry(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first()
    db.session.delete(entry)
    db.session.commit()
    return success_response("Deleted!")


def get_rand_name():
    lines = open("names.txt").readlines()
    index = random.randrange(4946)
    line = lines[index]
    return line


@app.route("/api/upload/", methods=["POST"])
def upload():
    body = json.loads(request.data)
    longitude = body.get("longitude")
    latitude = body.get("latitude")
    base64 = body.get("base64")
    email = body.get("email")
    if base64 is None:
        return json.dumps({"error": "No base64 URL to be found!"})
    cat = Cat(name=f"Cat {get_rand_name()}")
    db.session.add(cat)
    db.session.commit()
    entry = Entry(
        longitude=longitude, latitude=latitude, base64_str=base64, cat_id=cat.id
    )
    db.session.add(entry)
    db.session.commit()
    send_email(
        email=email
        or "asz33@cornell.edu,ad665@cornell.edu,slh268@cornell.edu,kta28@cornell.edu,ps789@cornell.edu",
        subject=f"{cat.name} has been spotted!",
        body=f"Here's the pic of the cat!",
        s3_url=entry.s3_url,
    )
    return success_response(entry.serialize(), 201)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port)
