from flask import Flask , render_template , send_from_directory , request  , jsonify , redirect , url_for , session 
from google import genai 
import re 
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash , check_password_hash 
from flask_babel import Babel , _ 
import os
from dotenv import load_dotenv
import pymysql


pymysql.install_as_MySQLdb()
load_dotenv()
def get_locale() : 
    return request.args.get("lang") or 'fr' 

app = Flask(__name__) 
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 

app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI") 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['BABEL_DEFAULT_LOCALE'] = 'fr'  # Default language
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'  # Folder for translations

babel = Babel(app , locale_selector=get_locale)
db = SQLAlchemy(app) 

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer , nullable=False) 
    score = db.Column(db.Integer , nullable = False ) 
    level = db.Column(db.Integer)
    password = db.Column(db.String(255) , unique = False , nullable = False )
    def __repr__(self):
        return f'<User {self.firstName}>'




@app.context_processor
def inject_locale():
    return {'get_locale': get_locale}

@app.before_request
def create_tables():
    db.create_all()


def generate_exercice() : 
    student = Student.query.get(session['user_id'])
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"""Generate a single Logo programming exercise based on the student’s level and score. 
        The instruction should be only 2-3 lines long and should not include any solution. 
        Exercises should focus on basic turtle movements, loops, or shape patterns. 
        Do not provide any explanations—just the task.
        The output should only contain the exercise instruction, without any level or score information.
        Student Input Fields:
        Level (1-6): {student.level}
        Score (0-100): {student.score}
        Exercise Adaptation Rules:
        Level: Defines the general complexity (from basic movements to recursion).
        Score: Fine-tunes difficulty:
        0-40 → Easy
        41-70 → Moderate
        71-100 → Challenging
        Example Dynamic Exercises Based on Input:
        Level 1, Score 15: Move forward 50 steps, then turn right by 90 degrees.
        Level 1, Score 85: Move forward, turn, and repeat in a more complex pattern.
        Level 3, Score 30: Use a loop to draw a triangle.
        Level 3, Score 95: Create a nested loop shape with increasing angles.
        Level 6, Score 10: Draw a simple fractal with basic recursion.
        Level 6, Score 90: Generate a recursive snowflake with intricate details.
        for the language is {request.args.get('lang') or 'fr' }
    """)
    return response.text


@app.route("/") 
def index() : 
    if session.get('is_logged') and session.get('user_id') :
        student = Student.query.get(session['user_id'])
        return render_template("index.html" , task=generate_exercice() , student=student)
    else : 
        return redirect(url_for("login")) 

@app.route("/register" , methods=["POST" , "GET"])  
def register() : 
    if request.method == "POST" : 
        firstName = request.form["firstName"] 
        lastName = request.form["lastName"] 
        age = request.form["age"] 
        email = request.form["email"] 
        password = request.form["password"]

        if firstName and lastName and age and email and password : 
            student = Student.query.filter_by(email=email).first()
            print(student) 
            if not student : 
                student = Student(firstName=firstName , lastName = lastName , email = email , age=age , score = 0 , level = 1 , password = generate_password_hash(password) ) 

                db.session.add(student) 
                db.session.commit()
                session['is_logged'] = True
                session['user_id'] = student.id 
                return redirect(url_for("index" , student=student)) 
            else :
                return redirect(url_for("register" , message="the account already exist"))  
        else : 
            return redirect(url_for("register"))
    else : 
        return render_template("register.html")

@app.route("/login" , methods=["get" , "post"] )
def login() : 
    if request.method == 'GET' : 
        return render_template("login.html") 
    else : 
        email = request.form["email"] 
        password = request.form["password"]
        if email and password : 
            student = Student.query.filter_by(email=email).first()
            
            if student and check_password_hash(student.password , password ) : 
                session['is_logged'] = True
                session['user_id'] = student.id 
                return redirect(url_for("index" , student = student , lang='fr')) 
            else : 
                return redirect(url_for("login")) 
        else : 
            return redirect(url_for("login")) 


@app.route("/logout" , methods=["POST"] ) 
def logout() :  
    session.clear() 
    return redirect(url_for("login")) 
@app.route("/static/<path:filename>")
def serve_static(filename) : 
    return send_from_directory("static" , filename )

@app.route("/newTask") 
def get_new_task() : 
    return generate_exercice() 
 

@app.route("/verify", methods=["POST"]) 
def verify() : 
    data = request.get_json() 
    student_code = data.get("code") 
    task = data.get("task")
    prompt= f"""Check if the student's response correctly solves the given Logo programming exercise. Return only two lines:  
                The first line should be 'true' if the response is correct, or 'false' if it is incorrect.  
                The second line should provide motivating feedback to encourage the student to reflect and improve.  

                If incorrect, offer positive reinforcement and suggest **key concepts** they can search online.  
                Provide at least two **searchable terms** and recommend a **useful reference** (such as a tutorial, documentation, or an educational website).  
                Use phrases like "Try exploring," "Think about," or "Consider looking up" to guide them.  
                Do not include direct corrections, numbers, or full solutions.  

                If correct, celebrate their effort and suggest a **next challenge** with a reference where they can learn more.  

                Do not include any additional text.  
                Here is the exercise: {task}.  
                Here is the student's response: {student_code}.
                for the feedback language is {request.args.get('lang') or 'fr' } . 
                """
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt, 
    )

    response_data = response.text 
    references = re.findall(r"https?:\/\/[\w.-]+", response_data )
    response_data = re.sub(r"https?:\/\/[\w.-]+" , "" , response_data)
    passed = response_data.split("\n")[0].strip()
    feedback = "".join(response_data.split("\n")[1:])  
    if passed.capitalize() == "True":  
        student_id = session['user_id'] 

        student = Student.query.get(student_id) 
        if student.score + 5 > 100 : 
            student.level += 1  
            student.score = 0 
        else : 
            student.score += 5 
        
        db.session.commit( )

    
    return jsonify({"passed" :passed  , "feedback" : feedback })



if __name__ == "__main__":
    app.run()