import os


class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'postgresql://Select-Context-5442:syhpun-xawpAr-seshe6@c7gljno857ucsl.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d240vgapnj5pks'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
