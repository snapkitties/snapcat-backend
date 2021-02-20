import json

from db import Entry
from db import db
from flask import Flask
from flask import request

app = Flask(__name__)
db_filename = "cats.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()


# generalized response formats
def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code


def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code


@app.route("/api/cats/")
def get_cats():
    # return success_response([c.serialize() for c in Course.query.all()])
    return success_response("hi")


@app.route("/api/upload/", methods=["POST"])
def upload():
    body = json.loads(request.data)
    longitude = body.get("longitude")
    latitude = body.get("latitude")
    base64 = body.get("base64")
    if base64 is None:
        return json.dumps({"error": "No base64 URL to be found!"})
    entry = Entry(longitude=longitude, latitude=latitude, base64=base64)
    db.session.add(entry)
    db.session.commit()
    return success_response(entry.serialize(), 201)

    # code = body.get("code")
    # name = body.get("name")
    # if not code or not name:
    #     return failure_response(
    #         "You must supply the code and name to create a course."
    #     )
    # new_course = Course(code=code, name=name)
    # db.session.add(new_course)
    # db.session.commit()
    # return success_response(new_course.serialize())
    return success_response("hi")


# @app.route("/api/courses/<int:course_id>/")
# def get_specific_course(course_id):
#     course = Course.query.filter_by(id=course_id).first()
#     if course is None:
#         return failure_response("Course not found!")
#     return success_response(course.serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
