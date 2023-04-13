from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.photo import VisionTextResource



app = Flask(__name__)


app.config.from_object(Config)
api = Api(app)



api.add_resource(VisionTextResource,'/vision')

api = Api(app)



if __name__ == '__main__' :
    app.run()