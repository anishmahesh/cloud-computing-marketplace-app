import os
import ast
from flask import request, make_response, abort
from flask import Flask, jsonify
from flask_api import status
from flask_restplus import Api, Resource, fields
from flask_mqtt import Mqtt
from models import Product, DataValidationError, DatabaseConnectionError
from werkzeug.exceptions import NotFound


DEBUG = False
PORT = os.getenv('PORT', '5000')

app = Flask(__name__)

# Configuring MQTT
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409


api = Api(app,
          version='1.0.0',
          title='Product Catalog REST API Service',
          description='This is a sample server Product store server.',
          doc='/apidocs/')

# This namespace is the start of the path i.e., /products
ns = api.namespace('products', description='Product operations')

# Define the model so that the docs reflect what can be sent
product_model = api.model('Product', {

    'id': fields.Integer(readOnly=True,
                         description='The unique id assigned internally by service'),
    'name': fields.String(required=True,
                          description='The name of the Product'),
    'category': fields.String(required=True,
                              description='The category of Product'),
    'price': fields.String(required=True,
                           description='The price of Product'),
    'description': fields.String(required=True,
                                 description='The description of Product'),
    'color': fields.String(required=True,
                           description='The color of Product'),
    'count': fields.Integer(readOnly=True,
                            description='The total count of Product')
})


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('myTopic')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print 'got msg'
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    payload = ast.literal_eval(data['payload'])
    if 'id' not in payload:
        print 'in post'
        create(payload)
    else:
        update(payload)


def create(payload):
    app.logger.info('Payload = %s', payload)
    prod = Product()
    prod.deserialize(payload)
    prod.save()
    app.logger.info('Product with new id [%s] saved!', prod.id)


def update(payload):
    p_id = payload['id']
    data = payload['payload']
    app.logger.info('Payload = %s', data)
    product = Product.find(p_id)
    if not product:
        raise NotFound(
            'Product with id [{}] was not found.'.format(p_id))
    app.logger.info('Product with id [%s] updated', p_id)
    product.deserialize(data)
    product.id = p_id
    product.save()



@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles all data validation issues from the model """
    message = error.message or str(error)
    return {'status': 400, 'error': 'Bad Request', 'message': message}, 400


@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """ Handles Database Errors from connection attempts """
    message = error.message or str(error)
    app.logger.critical(message)
    return {'status': 500, 'error': 'Server Error', 'message': message}, 500


@app.route('/healthcheck')
def healthcheck():
    """ Let them know our heart is still beating """
    return make_response(jsonify(status=200,
                                 message='Healthy'), status.HTTP_200_OK)



@app.route('/ui')
def index():
    """ Return something useful by default
    return jsonify(name='Product Demo REST API Service',
                   version='1.0',
                   url=url_for('list_product', _external=True)), HTTP_200_OK"""
    return app.send_static_file('index.html')


@ns.route('/<int:products_id>')
@ns.param('products_id', 'The Product identifier')
class ProductResource(Resource):
    """
    ProductResource class
    Allows the manipulation of a single Product
    GET /products{id} - Returns a Product with the id
    PUT /products{id} - Update a Product with the id
    DELETE /products{id} -  Deletes a Product with the id
    """

    @ns.doc('get_products`')
    @ns.response(404, 'Product not found')
    @ns.marshal_with(product_model)
    def get(self, products_id):
        """
        Retrieve a single Product
        This endpoint will return a Product based on it's id
        """
        app.logger.info(
            "Request to Retrieve a product with id [%s]", products_id)
        product = Product.find(products_id)
        if product:
            return product.serialize(), status.HTTP_200_OK
        else:
            raise NotFound(
                "Product with id '{}' was not found.".format(products_id))

    @ns.doc('update_products')
    @ns.response(404, 'Product not found')
    @ns.response(400, 'The posted Product data was not valid')
    @ns.expect(product_model)
    @ns.marshal_with(product_model)
    def put(self, products_id):
        """
        Update a Product
        This endpoint will update a Product based the body that is posted
        """
        app.logger.info(
            'Request to Update a product with id [%s]', products_id)
        check_content_type('application/json')
        data = dict(
            id=products_id,
            payload=api.payload
        )
        mqtt.publish('myTopic', str(data))
        product = Product()
        product.deserialize(data['payload'])
        product.id = products_id
        return product.serialize(), status.HTTP_200_OK

    @ns.doc('delete_products')
    @ns.response(204, 'Product deleted')
    def delete(self, products_id):
        """
        Delete a Product
        This endpoint will delete a Product based the id specified in the path
        """
        app.logger.info(
            'Request to Delete a product with id [%s]', products_id)
        product = Product.find(products_id)
        if product:
            product.delete()
        return '', HTTP_204_NO_CONTENT


@ns.route('/', strict_slashes=False)
class ProductCollection(Resource):
    @ns.doc('list_products')
    @ns.param('category', 'List Product by category')
    @ns.marshal_list_with(product_model)
    def get(self):
        app.logger.info('Request to list Products...')
        category = request.args.get('category')
        name = request.args.get('name')
        if category:
            results = Product.find_by_category(str(category).lower())
        elif name:
            results = Product.find_by_name(str(name).lower())
        else:
            results = Product.all()

        resultsUpd = [prod.serialize() for prod in results]

        return resultsUpd, status.HTTP_200_OK

    @ns.doc('create_products')
    @ns.expect(product_model)
    @ns.response(400, 'The posted data was not valid')
    @ns.response(201, 'Product created successfully')
    @ns.marshal_with(product_model, code=201)
    def post(self):

        app.logger.info('Request to Create a Product')
        check_content_type('application/json')
        prod = Product()
        app.logger.info('Payload = %s', api.payload)
        mqtt.publish('myTopic', str(api.payload))
        prod.deserialize(api.payload)
        location_url = api.url_for(
            ProductResource, products_id=prod.id, _external=True)
        return prod.serialize(), status.HTTP_201_CREATED, \
            {'Location': location_url}



@app.route('/products/available', methods=['GET'])
def list_available_products():
    results = Product.available()
    return make_response(jsonify([p.serialize() for p in results]),
                         HTTP_200_OK)


@app.route('/products/<int:id>/add_unit', methods=['PUT'])
def add_product_unit(id):
    product = Product.find(id)
    if product:
        product.count = int(product.count) + 1
        product.save()
        message = product.serialize()
        return_code = HTTP_200_OK
    else:
        message = {'error': 'Product with id: %s was not found' % str(id)}
        return_code = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), return_code)


@app.route('/products/<int:id>/sell_products', methods=['PUT'])
def sell_products(id):
    product = Product.find(id)
    if product:
        if product.count == 0:
            message = {
                'error': 'Product with id: %s is out of Stock' % str(id)}
        else:
            product.count = int(product.count) - 1
            product.save()
            message = product.serialize()

        return_code = HTTP_200_OK
    else:
        message = {'error': 'Product with id: %s was not found' % str(id)}
        return_code = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), return_code)


@app.route('/products/reset', methods=['DELETE'])
def products_reset():
    Product.remove_all()
    return make_response('', status.HTTP_204_NO_CONTENT)



def data_load(payload):
    Product(0, 'Asus2500', 'Laptop', '234',
            'Working Condition', 'Black', 23).save()
    Product(0, 'GE4509', 'Microwave', '45',
            'Open Box', 'Black', 12).save()
    Product(0, 'Hp', 'Microwave', '960', 'Brand New', 'Blue', 0).save()


def check_content_type(content_type):
    if request.headers['Content-Type'] == content_type:
        return
    app.logger.error('Invalid Content-Type: %s',
                     request.headers['Content-Type'])
    abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
          'Content-Type must be {}'.format(content_type))




@app.before_first_request
def init_db(redis=None):
    Product.init_db(redis)


def data_reset():
    Product.remove_all()


def get_product_data():

    init_db()
    data_reset()

    Product(0, 'Asus2500', 'Laptop', '234',
            'Working Condition', 'Black', 23).save()
    Product(0, 'GE4509', 'Microwave', '45',
            'Open Box', 'Black', 12).save()
    Product(0, 'Hp', 'Microwave', '960', 'Brand New', 'Blue', 0).save()

if __name__ == "__main__":
    get_product_data()
    app.run(host='0.0.0.0', port=int(PORT), debug=DEBUG)
