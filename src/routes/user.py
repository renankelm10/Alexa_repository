from flask import Blueprint, jsonify

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/profile', methods=['GET'])
def get_user_profile():
    return jsonify({"message": "User profile endpoint"})

@user_bp.route('/settings', methods=['POST'])
def update_user_settings():
    return jsonify({"message": "User settings updated"})

