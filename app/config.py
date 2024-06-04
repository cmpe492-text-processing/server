import os


class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'postgresql://ujqjl9jnt03pi:pa879e04a56186f7def8f333dad339afa0425bb478e68b3525714b0e048d443eb@cb889jp6h2eccm.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df6t0f9t2t8gsm'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 7200
    CACHE_THRESHOLD = 75000
