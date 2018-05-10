
import os
import json
import logging
import pickle
from redis import Redis
from cerberus import Validator
from redis.exceptions import ConnectionError



class DataValidationError(Exception):
    pass


class DatabaseConnectionError(Exception):
    pass


class BadRequestError(Exception):
    pass


class NotFoundError(Exception):
    pass




class Product(object):
    logger = logging.getLogger(__name__)
    redis = None
    schema = {
        'id': {'type': 'integer'},
        'name': {'type': 'string', 'required': True},
        'category': {'type': 'string', 'required': True},
        'price': {'type': 'integer', 'required': True},
        'description': {'type': 'string', 'required': True},
        'color': {'type': 'string', 'required': True},
        'count': {'type': 'integer', 'required': True}
    }
    __validator = Validator(schema)

    def __init__(self, id=0, name='', category='',
                 price='', description='', color='', count=''):
        self.id = int(id)
        self.name = name
        self.category = category
        self.price = price
        self.color = color
        self.description = description
        self.count = count

    def save(self):
        if self.id == 0:
            self.id = Product.__next_index()

        Product.redis.set(self.id, pickle.dumps(self.serialize()))

    def delete(self):
        Product.redis.delete(self.id)

    def serialize(self):
        return {"id": self.id, "name": self.name, "category": self.category,
                "price": self.price, "description": self.description,
                "color": self.color, "count": self.count}

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.category = data['category']
            self.price = data['price']
            self.description = data['description']
            self.color = data['color']
            self.count = data['count']
        except KeyError as err:
            raise DataValidationError(
                'Invalid product: missing ' + err.args[0])
        except TypeError:
            raise DataValidationError(
                'Invalid product: body of request contained bad or no data')
        return self


    @staticmethod
    def __next_index():
        return Product.redis.incr('index')

    @staticmethod
    def all():
        results = []
        for key in Product.redis.keys():
            if key != 'index':
                data = pickle.loads(Product.redis.get(key))
                product = Product(data['id']).deserialize(data)
                results.append(product)
        return results

    @staticmethod
    def available():
        results = []

        for key in Product.redis.keys():
            if key != 'index':
                data = pickle.loads(Product.redis.get(key))
                product = Product(data['id']).deserialize(data)

                if product.count > 0:
                    results.append(product)
        return results

    @staticmethod
    def remove_all():
        Product.redis.flushall()


    @staticmethod
    def find(product_id):
        if Product.redis.exists(product_id):
            data = pickle.loads(Product.redis.get(product_id))
            product = Product(data['id']).deserialize(data)
            return product
        return None

    @staticmethod
    def __find_by(attribute, value):
        Product.logger.info('Processing %s query for %s', attribute, value)
        search_criteria = value.lower()
        results = []
        for key in Product.redis.keys():
            if key != 'index':
                data = pickle.loads(Product.redis.get(key))
                test_value = data[attribute].lower()
                if test_value == search_criteria:
                    results.append(Product(data['id']).deserialize(data))
        return results

    @staticmethod
    def find_by_category(category):
        return Product.__find_by('category', category)

    @staticmethod
    def find_by_name(name):
        return Product.__find_by('name', name)


    @staticmethod
    def connect_to_redis(hostname, port, password):
        Product.logger.info("Testing Connection to: %s:%s", hostname, port)
        Product.redis = Redis(host=hostname, port=port, password=password)
        try:
            Product.redis.ping()
            Product.logger.info("Connection established")
        except ConnectionError:
            Product.logger.info("Connection Error from: %s:%s", hostname, port)
            Product.redis = None
        return Product.redis

    @staticmethod
    def init_db(redis=None):
        if redis:
            Product.logger.info("Using client connection...")
            Product.redis = redis
            try:
                Product.redis.ping()
                Product.logger.info("Connection established")
            except ConnectionError:
                Product.logger.error("Client Connection Error!")
                Product.redis = None
                raise ConnectionError('Could not connect to the Redis Service')
            return

        if 'VCAP_SERVICES' in os.environ:
            Product.logger.info("Using VCAP_SERVICES...")
            vcap_services = os.environ['VCAP_SERVICES']
            services = json.loads(vcap_services)
            creds = services['rediscloud'][0]['credentials']
            Product.logger.info("Conecting to Redis on host %s port %s",
                                creds['hostname'], creds['port'])
            Product.connect_to_redis(creds['hostname'], creds[
                                     'port'], creds['password'])
        else:
            Product.logger.info(
                "VCAP_SERVICES not found, checking localhost for Redis")
            Product.connect_to_redis('127.0.0.1', 6379, None)
            if not Product.redis:
                Product.logger.info(
                    "No Redis on localhost, looking for redis host")
                Product.connect_to_redis('redis', 6379, None)
        if not Product.redis:
            Product.logger.fatal(
                '*** FATAL ERROR: Could not connect to the Redis Service')
            raise ConnectionError('Could not connect to the Redis Service')
