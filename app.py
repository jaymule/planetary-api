from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)

# will put the database file in the same folder as the running application
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuring config variable SQLALCHEMY_DATABASE_URI (File based database)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')

app.config['JWT_SECRET_KEY'] = 'super-secret'
#app.config['JWT_ALGORITHM'] = 'HS256'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'ffac90612d8cd8'
app.config['MAIL_PASSWORD'] = '743c231c692027'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
# app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
# app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']


# initialization of database
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database created!!")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("Database dropped!!")


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516.0,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sol',
                   mass=4.867e24,
                   radius=3760.0,
                   distance=67.24e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.972e24,
                   radius=3959.0,
                   distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William',
                     last_name='Herschel',
                     email='test@test.com',
                     password='P@ssw0rd')

    db.session.add(test_user)
    db.session.commit()
    print("Database seeded!")


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type',
                  'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


@app.route('/')
def hello():
    return jsonify("Hello World! Haha nope")


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message=f"Sorry {name}, you are not old enough"), 401
    else:
        return jsonify(message=f"Welcome {name}!!")


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    # name = request.args.get('name')
    # age = request.args.get('age')
    if age < 18:
        return jsonify(message=f"Sorry {name}, you are not old enough"), 401  # Unauthorized
    else:
        return jsonify(message=f"Welcome {name}!!")


@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    # planet_list = []
    # for planet in planets:
    #     planet_data = {'planet_id': planet.planet_id,
    #                     'planet_name': planet.planet_name,
    #                     'planet_type': planet.planet_type,
    #                     'home_star': planet.home_star,
    #                     'mass': planet.mass,
    #                     'radius': planet.radius,
    #                     'distance': planet.distance}
    #     planet_list.append(planet_data)

    # serializing sql object
    res = planets_schema.dump(planets)
    return jsonify(Planets=res)


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    all_users = users_schema.dump(users)
    return jsonify(all_users)


@app.route('/register', methods=['POST'])
def register_user():
    email = request.json['email']
    test = User.query.filter_by(email=email).first()

    if test:
        return jsonify(message="That email already exists."), 409  # conflict
    else:
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        password = request.json['password']
        user = User(first_name=first_name, last_name=last_name, email=email,
                    password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User create successfully."), 201  # resource created


@app.route('/login', methods=['POST'])
def user_login():
    email = ""
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    # first() method will return the first matching record from database
    test = User.query.filter_by(email=email, password=password).first()

    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded..!!", access_token=access_token)
    else:
        return jsonify(message="Incorrect email or password."), 401  # Unauthorized


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_pass(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your planetary api password is " + user.password,
                      sender="admin@planeraty-api.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="That email doesn't exist."), 401  # Unauthorized


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id: int):
    data = Planet.query.filter_by(planet_id=planet_id).first()

    if data:
        res = planet_schema.dump(data)
        return jsonify(Planet=res)
    else:
        return jsonify(message="Planet does not exist.!"), 404  # not found


@app.route('/planets', methods=['POST'])
@jwt_required
def add_planet():
    name = request.json['planet_name']
    check = Planet.query.filter_by(planet_name=name).first()
    if check:
        return jsonify(message=name + " planet already exist"), 409  # conflict

    id = request.json['planet_id']
    type = request.json['planet_type']
    home_star = request.json['home_star']
    mass = float(request.json['mass'])
    radius = float(request.json['radius'])
    distance = float(request.json['distance'])

    new_planet = Planet(planet_id=id, planet_name=name,
                        planet_type=type, home_star=home_star,
                        mass=mass, radius=radius, distance=distance)
    db.session.add(new_planet)
    db.session.commit()
    return jsonify(message=name + " planet added."), 201  # resource created


@app.route('/update_planet', methods=['PUT'])
def update_planet():
    planet_id = request.json['planet_id']
    planet = Planet.query.filter_by(planet_id=planet_id).first()

    if planet.planet_name != request.json['planet_name']:
        planet.planet_name = request.json['planet_name']
        planet.planet_type = request.json['planet_type']
        planet.home_star = request.json['home_star']
        planet.mass = float(request.json['mass'])
        planet.distance = float(request.json['distance'])
        planet.radius = float(request.json['radius'])
        db.session.commit()
        return jsonify(message="Planet updated"), 202  # resource data update success

    else:
        return jsonify(message="The planet either already added or does not exist."), 404


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
def remove_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="Planet deleted.."), 202  # change accepted
    else:
        return jsonify(message="Planet does not exist"), 404


if __name__ == '__main__':
    app.run(debug=True)
