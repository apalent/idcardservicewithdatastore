from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///id_card_database.db'
db = SQLAlchemy(app)


class IDCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    date_of_birth = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)

    def __init__(self, name, bank_name, phone_number, date_of_birth, blood_group):
        self.name = name
        self.bank_name = bank_name
        self.phone_number = phone_number
        self.date_of_birth = date_of_birth
        self.blood_group = blood_group


# Initialize the database within the application context
with app.app_context():
    db.create_all()


@app.route('/id_card', methods=['POST'])
def save_id_card():
    data = request.json
    name = data['name']
    bank_name = data['bank_name']
    phone_number = data['phone_number']
    date_of_birth = data['date_of_birth']
    blood_group = data['blood_group']

    id_card = IDCard(name=name, bank_name=bank_name, phone_number=phone_number,
                     date_of_birth=date_of_birth, blood_group=blood_group)

    db.session.add(id_card)
    db.session.commit()

    return jsonify({"message": "ID card details saved successfully"}), 201


@app.route('/id_card/<string:phone_number>', methods=['GET'])
def get_id_card(phone_number):
    id_card = IDCard.query.filter_by(phone_number=phone_number).first()
    if id_card:
        return jsonify({
            "name": id_card.name,
            "bank_name": id_card.bank_name,
            "phone_number": id_card.phone_number,
            "date_of_birth": id_card.date_of_birth,
            "blood_group": id_card.blood_group
        })
    else:
        return jsonify({"message": "ID card not found"}), 404


@app.route('/id_card/<string:phone_number>', methods=['PUT'])
def edit_id_card(phone_number):
    id_card = IDCard.query.filter_by(phone_number=phone_number).first()
    if id_card:
        data = request.json
        id_card.name = data['name']
        id_card.bank_name = data['bank_name']
        id_card.date_of_birth = data['date_of_birth']
        id_card.blood_group = data['blood_group']

        db.session.commit()
        return jsonify({"message": "ID card details updated successfully"}), 200
    else:
        return jsonify({"message": "ID card not found"}), 404


@app.route('/id_card/<string:phone_number>', methods=['DELETE'])
def delete_id_card(phone_number):
    id_card = IDCard.query.filter_by(phone_number=phone_number).first()
    if id_card:
        db.session.delete(id_card)
        db.session.commit()
        return jsonify({"message": "ID card deleted successfully"}), 200
    else:
        return jsonify({"message": "ID card not found"}), 404


if __name__ == '__main__':
    app.run()
