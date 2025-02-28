from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from datetime import datetime

app = Flask(__name__)

# Configure MySQL Database (Replace with your actual XAMPP MySQL credentials)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/energy_forecast"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"

# Initialize Database & Encryption
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# =========================== DATABASE MODELS =========================== #
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

class EnergyForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    solar_energy = db.Column(db.Float, nullable=False)
    wind_energy = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================== USER AUTH ROUTES =========================== #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        location = request.form["location"]

        user = User(username=username, password=password, location=location)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials!"
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================== WEATHER API & PREDICTION =========================== #
def fetch_weather_data(location):
    API_KEY = "your_openweathermap_api_key"  # Replace with actual API Key
    URL = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}"

    try:
        response = requests.get(URL)
        response.raise_for_status()
        data = response.json()
        
        sunlight_intensity = data["clouds"]["all"]
        wind_speed = data["wind"]["speed"]
        temperature = data["main"]["temp"] - 273.15  # Convert from Kelvin to Celsius
        
        return sunlight_intensity, wind_speed, temperature
    except requests.exceptions.RequestException as e:
        print("Error fetching weather data:", e)
        return None

def predict_energy(location):
    weather_data = fetch_weather_data(location)
    if weather_data is None:
        return None

    sunlight_intensity, wind_speed, temperature = weather_data

    # Dummy prediction formula (Replace with ML model)
    solar_energy = (100 - sunlight_intensity) * 0.2
    wind_energy = wind_speed * 0.5

    return {"solar_energy": round(solar_energy, 2), "wind_energy": round(wind_energy, 2)}

@app.route("/forecast", methods=["GET"])
@login_required
def forecast_energy():
    prediction = predict_energy(current_user.location)
    if not prediction:
        return jsonify({"error": "Failed to fetch data"}), 500

    # Save forecast data in database
    forecast = EnergyForecast(
        user_id=current_user.id,
        date=datetime.now().strftime("%Y-%m-%d"),
        solar_energy=prediction["solar_energy"],
        wind_energy=prediction["wind_energy"]
    )
    db.session.add(forecast)
    db.session.commit()

    return jsonify(prediction)

# =========================== DASHBOARD ROUTE =========================== #
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# =========================== RUN FLASK SERVER =========================== #
if __name__ == "__main__":
    db.create_all()  # Ensure database tables are created
    app.run(debug=True)
