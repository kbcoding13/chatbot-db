from platform import android_ver

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.sql.functions import current_user

from models import db, User, Conversation, Message
from dotenv import load_dotenv
import anthropic
import bcrypt
import os

app = Flask(__name__)

load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://postgres:{os.getenv('PSQL_PASSWORD')}@localhost/postgres"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(name=name, email=email, password_hash=password_hash)

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 201

@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error':'PLease fill an email and a password'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error':'This email or password does not exist'}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/users/<int:user_id>',methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'This user does not exist'}), 404

    return jsonify(user.to_dict())

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Please enter a name and email'}), 404

    user = User(name=name, email=email)

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()),201

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.get_or_404(user_id)

    if user is None:
        return jsonify({'error': 'Username does not exist'})

    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict()), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'error': 'Username does not exist'})

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'user has been successfully deleted'})


@app.route('/users/search', methods=['GET'])
def search_users():
    name = request.args.get('name')
    if not name:
        return jsonify({'error':'name query parameter required'}), 400

    users = User.query.filter(User.name.ilike(f'%{name}%')).all()
    return jsonify([u.to_dict() for u in users])


@app.route('/conversations', methods=['POST'])
def create_conversation():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'This user does not exist'}), 404

    conversation = Conversation(user_id=user_id)
    db.session.add(conversation)
    db.session.commit()

    return jsonify(conversation.to_dict()), 201

@app.route('/conversations/<int:conversation_id>/chat', methods=['POST'])
@jwt_required()
def chat(conversation_id):
    current_user_id = int(get_jwt_identity())
    conversation = Conversation.query.get(conversation_id)
    if conversation is None:
        return jsonify({'error': 'This conversation does not exist'}), 404

    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No messages present'}), 400

    user_msg = Message(
        conversation_id=conversation_id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.flush()

    history = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.created_at.asc()).all()

    claude_messages = [
        {'role': m.role, 'content': m.content} for m in history
    ]

    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=claude_messages
    )

    assistant_reply = response.content[0].text

    assistant_msg = Message(
        conversation_id=conversation_id,
        role='assistant',
        content=assistant_reply
    )

    db.session.add(assistant_msg)
    db.session.commit()


    return jsonify({
        'user_message': user_message,
        'assistant_reply': assistant_reply
    }), 200

if __name__ == "__main__":
    app.run(debug=True)