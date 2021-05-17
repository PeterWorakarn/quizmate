from flask import Flask, render_template, redirect, request, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from passlib.hash import sha256_crypt
import os # use in join path and duplicate file
import shutil # for copy file
import functionX as func

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)    # create database object
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(100))
    model_name = db.Column(db.String(200))
    question = db.Column(db.String(1000))

@login_manager.user_loader #call user information by user id
def load_user(user_id):
        # receive user_id and return all data in that id
    return User.query.get(int(user_id)) 

################################################ 
# LANDING PAGE AND INFO PAGE
################################################
@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
@login_required
def admin():
    if current_user.username != 'Worakarn':
        return redirect(url_for('index'))
    else:
        data = User.query.all()
        count_answer_all = {}
        #print (data)
        for each in data: #read raw_data for each of user
            #print (each)
            username = each.username
            try:
                raw_data_directory = os.path.join('user_project',username, 'raw_data.json')
                result = func.read_json_file(raw_data_directory)
                result = result['raw_data']
                count_answer_all[username] = len(result)
            except FileNotFoundError: 
                count_answer_all[username] = 0
        print (count_answer_all)
        return render_template('admin.html', data = data, count_answer_all = count_answer_all)

################################################ 
# AUTHENTICATION 
################################################

@app.route('/login', methods = ['GET','POST'])  
def login():
    if current_user.is_authenticated:
        flash('You are already logged in','success')
        return redirect(url_for('dashboard'))
    if request.method =="POST":
        email = request.form['email']
        result = User.query.filter_by(email=email).first()
        if result == None:
            flash("There isn't an account for this email",'danger')
            return redirect(url_for('login'))
        else:
            password_candidate = request.form['password']
            password = result.password #Access the password in database
            if sha256_crypt.verify(password_candidate,password):
                flash('Welcome, back','success') 
                #user = result.username
                #print (user)
                login_user(result) 
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong password, Try again",'danger')
                return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/register',methods = ['GET','POST'])    
def register():
    if current_user.is_authenticated:   #check is it authen?
        flash('You are already logged in','success')
        return redirect(url_for('dashboard'))
    if request.method =="POST": #check method POST that send by url_for
        password = request.form['password']
        confirm_password = request.form['confirm']
        if password != confirm_password:
            flash("Password don't match, Try again",'danger') #use includes _messages to flash in specific page
            return redirect(url_for('register'))
        else:
            username = request.form['username']
            result = User.query.filter_by(username=username).first() 
            if result != None: #find some value when query
                flash("This username already uses, Please use a different username",'danger')
                return redirect(url_for('register'))
            else:
                email = request.form['email']
                result = User.query.filter_by(email=email).first() 
                #print (result)
                if result != None: #find some value when query
                    flash("This email already uses, Please use a different email",'danger')
                    return redirect(url_for('login'))
                else:
                    password = request.form['password']
                    password = sha256_crypt.encrypt(str(password))
                    user = User(username = username,email = email, password = password)
                    db.session.add(user) #add user_data to the database
                    db.session.commit() 

                    flash("Registration successful, Now you can login",'success')
                    return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/logout')
@login_required #require login first to access this function
def logout():
    logout_user()   # log out function
    flash ('You are now logged out','success')
    return redirect(url_for('login'))

################################################ 
# DASHBOARD 
################################################

@app.route('/dashboard') # create required file for user (this process cannot repeatable)
@login_required
def dashboard():
    username = current_user.username
    folder_project = os.path.join('user_project', username)
    try:    #create directory 
        os.mkdir(folder_project)
        ## copy dataset file
        original_file = 'rasa_dataset.json'
        filename = 'dataset.json'
        destination_file = os.path.join('user_project',username, filename)   
        shutil.copy(original_file, destination_file)

        ## copy raw_data file
        original_file = 'raw_data.json'
        filename = 'raw_data.json'
        destination_file = os.path.join('user_project',username, filename)   
        shutil.copy(original_file, destination_file)

        ## copy predict_data file
        original_file = 'predict_data.json'
        filename = 'predict_data.json'
        destination_file = os.path.join('user_project',username, filename)   
        shutil.copy(original_file, destination_file)

        return render_template('dashboard.html')
    except FileExistsError: #if replace same directory will redirect to dashboard
        raw_data_directory = os.path.join('user_project',username, 'raw_data.json')
        ## save to file
        result = func.read_json_file(raw_data_directory)
        result = result['raw_data']
        count_answer = (len(result))
        return render_template('dashboard.html',count_answer = count_answer)
    return render_template('dashboard.html')

################################################ 
# CREATE QUIZ
################################################
@app.route('/create_quiz',methods = ['GET','POST'])
@login_required #require login first to access this function
def create_quiz():
    if request.method =="POST": #check method POST that send by url_for
        model_name = request.form['model_name']
        result = User.query.filter_by(model_name = model_name).first()
        if result != None: #find some value when query
            flash("This project name already uses, Please use a different name",'danger')
            return render_template('create_quiz.html')
        #### Add question and model_name to database####
        else:
            username = current_user.username
            question = request.form['question'] #request and assign in variable
            result = User.query.filter_by(username=username).first() #find row by username column
            result.model_name = model_name #write value in model_name column
            result.question = question  #write value in question column
            db.session.add(result) #add user_data to the database
            db.session.commit() #add back to database

            #### Add new intent ####
            text_intent = {}
            data = request.form #store form(dict) in data
            print (data)
            count = int(data['contacts'])

            for i in range(1,count+1): #run loop to find fill form
                text = "text" +"-"+ str(i)
                intent = "intent"+"-"+ str(i)
                if len(data[text]) <= 0: #filter only form that isnot contain value
                    print ("this is empty")
                else: #add form with value
                    text_intent[data[text]] = data[intent]
            print(text_intent)

            ### add text / intent to dataset ####
            dataset_directory = os.path.join('user_project',username, 'dataset.json')
            for i in text_intent:
                text = i
                intent = text_intent[i]
                print (func.add_dataset(text,intent,dataset_directory)) # add one by one
                        
            #### Train model ####
            model_name_directory = os.path.join('user_project',username, model_name)
            print (func.train_model(dataset_directory, model_name, model_name_directory))    
            return redirect(url_for('publish_quiz'))
    return render_template('create_quiz.html')

@app.route('/publish_quiz')
@login_required
def publish_quiz():
    if current_user.question == None:
        return redirect(url_for('create_quiz'))
    model_name = current_user.model_name
    return render_template('publish_quiz.html',model_name = model_name)

################################################ 
# ADD MORE
################################################
@app.route('/add_more',methods = ['POST','GET'])
@login_required
def add_more():
    if request.method =="POST": 
        text_intent = {}
        data = request.form #store form(dict) in data
        print (data)
        count = int(data['contacts'])
        for i in range(1,count+1): #run loop to find fill form
            text = "text" +"-"+ str(i)
            intent = "intent"+"-"+ str(i)
            if len(data[text]) <= 0: #filter only form that isnot contain value
                print ("this is empty")
            else: #add form with value
                text_intent[data[text]] = data[intent]
        print(text_intent)
        ### extract dataset from form ####
        username = current_user.username
        model_name = current_user.model_name
        dataset_directory = os.path.join('user_project',username, 'dataset.json')
        model_name_directory = os.path.join('user_project',username, model_name)
        ### add text / intent to dataset ####
        for i in text_intent:
            text = i
            intent = text_intent[i]
            print (func.add_dataset(text,intent,dataset_directory)) # add one by one
        ### train model
        print (func.train_model(dataset_directory, model_name, model_name_directory)) 
        flash('Add answer examples success','success')
        return redirect(url_for('dashboard'))
    return render_template('add_more.html')

################################################ 
# ANSWER QUIZ
################################################
@app.route('/access_quiz',methods = ['POST', 'GET'])
def access_quiz():
    if request.method =="POST": 
        model_name = request.form['model_name'] 
        result = User.query.filter_by(model_name = model_name).first()
        if result != None:  #detect access code in db
            question = result.question
            return render_template('answer_quiz.html',model_name = model_name, question = question)
        else:      #undetect access code in db
            flash("Access code not found, Try again",'danger')
            return render_template('access_quiz.html')
    return render_template('access_quiz.html')

@app.route('/answer_quiz',methods = ['POST']) #METHOD Not allow for direct to specific page or refresh
def answer_quiz():
    if request.method =="POST": #check method POST that send by url_for
        name = request.form['name'] #request and assign in variable
        surname = request.form['surname'] #request and assign in variable
        new_name = name + " " + surname
        new_answer = request.form['answer_response'] #request and assign in variable
        model_name = request.form['model_name']
        result = User.query.filter_by(model_name = model_name).first()
        username = result.username
        raw_data_directory = os.path.join('user_project',username, 'raw_data.json')
        print (func.add_answer(new_name,new_answer,raw_data_directory))
        return render_template('answer_success.html')
   

################################################ 
# PREDICTION AND RETRAIN MODEL 
################################################
@app.route('/overall_prediction') 
@login_required
def overall_prediction():
    username = current_user.username
    model_name = current_user.model_name
    raw_data_directory = os.path.join('user_project',username, 'raw_data.json')
    predict_data_directory = os.path.join('user_project',username, 'predict_data.json')
    model_name_directory = os.path.join('user_project',username, model_name,'default', model_name)
    ## predict model
    print (func.predict_model(raw_data_directory,model_name_directory,predict_data_directory))
    ## save to file
    predictresult = func.read_json_file(predict_data_directory)
    result = predictresult['predict_data']
    return render_template('overall_prediction.html',data = result)

@app.route('/view/<string:id>',methods=['GET']) 
@login_required
def view_prediction(id): 
    username = current_user.username
    predict_data_directory = os.path.join('user_project',username, 'predict_data.json')
    predict_result = func.read_json_file(predict_data_directory)
    view_info = predict_result['predict_data'][id]
    return render_template('view_prediction.html', info = view_info, id = id)

@app.route('/edit/<string:answer_data>/<string:intent_data>/<string:id>',methods=['GET']) 
@login_required
def edit_intent(answer_data,intent_data,id):                            
    return render_template('edit_intent.html', text = answer_data, intent = intent_data, id = id)

@app.route('/change_intent',methods=['POST'])
@login_required
def change_intent():
    if request.method =="POST": #check method POST that send from add.html by url_for
        username = current_user.username
        model_name = current_user.model_name
        text = request.form['text'] 
        intent = request.form['new_intent'] 
        dataset_directory = os.path.join('user_project',username, 'dataset.json')
        model_name_directory = os.path.join('user_project',username, model_name)
        print (func.add_dataset(text,intent,dataset_directory))
        print (func.train_model(dataset_directory, model_name, model_name_directory))  
        flash('Change answer tag success','success')
        return redirect(url_for('overall_prediction'))

################################################ 
# EXPORT FILE
################################################
@app.route('/export_file') 
@login_required
def export_file():
    username = current_user.username
    predict_data_directory = os.path.join('user_project',username, 'predict_data.json')
    csv_directory = os.path.join('user_project',username, 'predict_report.csv')
    print (func.export_csv_file(predict_data_directory, csv_directory))
    return send_file(csv_directory,as_attachment=True)


################################################ 
# ERROR
################################################
@app.errorhandler(404) #get 404 code page not found to render at here
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(401)  #401 error is unauthorize access
def Unauthorize_access(e):
    return redirect(url_for('login'))

@app.errorhandler(405)  #405 error is method not allow refresh form page without get
def Method_not(e):
    return redirect(url_for('access_quiz'))  



#200 success