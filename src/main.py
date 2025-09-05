from flask import Flask, request, jsonify
from src.routes.alexa import alexa_bp
from src.services.n8n_integration import send_to_n8n # Importe a função send_to_n8n

# Importe o blueprint de usuário
from src.routes.user import user_bp

# Se você precisa de 'db' de src.models.user, importe-o aqui.
# Se não, a linha abaixo pode ser removida ou comentada se você não for usar um ORM.
# from src.models.user import db # Descomente se você realmente tiver um 'db' lá

app = Flask(__name__)

# Registre os blueprints
app.register_blueprint(alexa_bp, url_prefix='/alexa')
app.register_blueprint(user_bp, url_prefix='/api/user') # Exemplo de prefixo para rotas de usuário

@app.route('/')
def home():
    return "Alexa Skill Backend is running!"

@app.route('/api/health')
def health_check():
    return jsonify({"service": "alexa-skill", "status": "healthy"})

# Você pode adicionar outras rotas ou lógica aqui, se necessário

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

