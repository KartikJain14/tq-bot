from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per hour"],
    storage_uri="memory://",
)

client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
db = client["discord_bot"]
participants_collection = db["participants"]

# Route for the home page
@limiter.limit("20 per hour")
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@limiter.limit("60 per hour")
@app.route("/favicon.ico")
@app.route("/bg.png")
def favicon():
    return app.send_static_file(request.path[1:])

# Route to handle the form submission
@limiter.limit("10 per hour")
@app.route("/get", methods=["GET"])
def submit():
    email = request.args.get("email")
    participant = participants_collection.find_one({"email": email})
    
    if not participant:
        return jsonify({"message": "We couldn't find your details, Please contact the organizers."})
    else:
        # Send participant details to the response page
        return render_template("response.html", name=participant["name"], team_number=participant["team_number"], invite_link=participant["invite_link"])

# Run the app on port 3000
if __name__ == "__main__":
    app.run(port=os.getenv("PORT", 3000))
