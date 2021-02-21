import base64
import boto3
import datetime
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
from PIL import Image
import random
import re
import string

db = SQLAlchemy()

EXTENSIONS = ["png", "gif", "jpg", "jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET = "snapkitties"
S3_BASE_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"


class Cat(db.Model):
    __tablename__ = "cat"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    entries = db.relationship("Entry", cascade="delete")

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.entries = []

    def serialize(self):
        return {"id": self.id, "entries": [entry.serialize() for entry in self.entries]}


class Entry(db.Model):
    __tablename__ = "entry"
    id = db.Column(db.Integer, primary_key=True)
    longitude = db.Column(db.String, nullable=False)
    latitude = db.Column(db.String, nullable=False)
    s3_url = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cat = db.Column(db.Integer, db.ForeignKey("cat.id"), nullable=True)

    def __init__(self, **kwargs):
        self.create(kwargs.get("base64_str"))
        self.longitude = kwargs.get("longitude")
        self.latitude = kwargs.get("latitude")
        self.cat = kwargs.get("cat_id", -1)

    def serialize(self):
        return {
            "id": self.id,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "s3_url": self.s3_url,
            "created_at": str(self.created_at),
        }

    def create(self, base64_str):
        # [1:] strips off leading period
        ext = guess_extension(guess_type(base64_str)[0])[1:]
        if ext not in EXTENSIONS:
            raise Exception(f"Extension {ext} not supported!")

        # secure way of generating random string for image name
        salt = "".join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(16)
        )

        # remove header of base64_str string
        img_str = re.sub("^data:image/.+;base64,", "", base64_str)
        img_data = base64.b64decode(img_str)
        img = Image.open(BytesIO(img_data))

        # create db object
        self.s3_url = f"{S3_BASE_URL}/{salt}.{ext}"
        self.created_at = datetime.datetime.now()

        # upload image to AWS
        img_filename = f"{salt}.{ext}"
        self.upload(img, img_filename)

    def upload(self, img, img_filename):
        # save image temporarily
        img_temploc = f"{BASE_DIR}/{img_filename}"
        img.save(img_temploc)

        # upload image to S3
        s3_client = boto3.client("s3")
        s3_client.upload_file(img_temploc, S3_BUCKET, img_filename)

        # make S3 image url public
        s3_resource = boto3.resource("s3")
        object_acl = s3_resource.ObjectAcl(S3_BUCKET, img_filename)
        object_acl.put(ACL="public-read")
        os.remove(img_temploc)
