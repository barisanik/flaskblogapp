from math import log
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
import flask_sqlalchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import datetime
from functools import wraps #decorator ile giriş kontrolü için
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Barış/Desktop/cleanBlogForServer/blog.db'
app.secret_key = "myblog"
db = SQLAlchemy(app)

#Database tables
#user table
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    email = db.Column(db.String)
    last_activity = db.Column(db.DateTime)
    register_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
# articles table
class articles(db.Model):
    artID = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String)
    author = db.Column(db.String)
    content = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

#Login check decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın!","danger")
            return redirect(url_for("loginPage"))
    return decorated_function

#Forms
#Register page form
class RegisterForm(Form):
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min=4, max=20)])
    password = PasswordField("Parola", validators=[
        validators.DataRequired(message= "Lütfen bir parola belirleyin."),
        validators.Length(min=4, max=20, message="Parola en az 4 en fazla 20 haneli olmalıdır."),
        validators.EqualTo(fieldname="confirm",message="Parolanız tekrarıyla uyuşmalıdır.")
    ])
    confirm = PasswordField("Parola tekrarı")
    email = StringField("Mail Adresi", validators=[ validators.Email(message = "Lütfen geçerli bir mail adresi girin.")])

#Login Page Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

#Reset Password Form
class ResetPassForm(Form):
    username = StringField("Kullanıcı Adınız")
    newpass = PasswordField("Parola", validators=[
        validators.DataRequired(message= "Lütfen bir parola belirleyin."),
        validators.Length(min=4, max=20, message="Parola en az 4 en fazla 20 haneli olmalıdır."),
        validators.EqualTo(fieldname="confirm",message="Parolanız tekrarıyla uyuşmalıdır.")
    ])
    newpassagain = PasswordField("Parola (Tekrar)", validators=[
        validators.DataRequired(message= "Lütfen bir parola belirleyin."),
        validators.Length(min=4, max=20, message="Parola en az 4 en fazla 20 haneli olmalıdır."),
        validators.EqualTo(fieldname="confirm",message="Parolanız tekrarıyla uyuşmalıdır.")
    ])

# Article Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators = [validators.Length(min=5, max=100)])
    content = TextAreaField("Makale İçeriği", validators = [validators.Length(min=20)] ) #Büyük yer kaplayabileceği için TextAreaField seçildi.
    

@app.route("/")
def indexPage():
    return render_template("index.html")

@app.route("/about")  
def aboutBlogPage():
    return render_template("about.html")

@app.route("/register", methods = ["GET", "POST"])
def registerPage():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        regUsername = form.username.data
        userInfoCheck = users.query.filter_by(username=regUsername).first()
        if userInfoCheck:
            flash("Belirtilen kullanıcı adı mevcut!","danger")
        else:
            regPass = sha256_crypt.encrypt(form.password.data)
            regMail = form.email.data
            regDate = datetime.datetime.now()
            registerSQL = users(username = regUsername, password = regPass, email = regMail, last_activity = regDate, register_date = regDate)
            db.session.add(registerSQL)
            db.session.commit()
            flash("Başarıyla Kayıt Oldunuz!","success")
            return redirect(url_for("indexPage"))
    else:
        pass
    return render_template("register.html", form=form)

@app.route("/login", methods = ["GET", "POST"])
def loginPage():
    form = LoginForm(request.form)
    if request.method == "POST":
        logUsername = form.username.data
        password_ent = form.password.data
        userInfoCheck = users.query.filter_by(username=logUsername).first()
        if userInfoCheck:
            if sha256_crypt.verify(password_ent, userInfoCheck.password):
                flash("Başarıyla giriş yapıldı!","success")
                session["logged_in"] = True       
                session["username"] = logUsername
                currentdate = datetime.datetime.now()
                userInfoCheck.last_activity = currentdate
                db.session.commit()
                return redirect(url_for("indexPage"))
            else:
                flash("Yanlış şifre. Tekrar deneyin.","danger")
                return redirect(url_for("loginPage"))
                
        else:
            flash("Belirtilen kullanıcı adıyla kimse bulunamadı.","danger")
            return redirect(url_for("loginPage"))

    return render_template("login.html", form=form)

@app.route("/logout") 
def logoutPage():
    userInfoCheck = users.query.filter_by(username=session["username"]).first()
    currentdate = datetime.datetime.now()
    userInfoCheck.last_activity = currentdate
    db.session.commit()
    session.clear()
    flash("Başarıyla çıkış yapıldı.","success")
    return redirect(url_for("indexPage"))

@app.route("/user/<string:username>")
@login_required
def userProfile(username):
    userInfoCheck = users.query.filter_by(username=username).first()
    if userInfoCheck:
        userArticlesCheck = articles.query.filter_by(author=userInfoCheck.username).all()
        return render_template("user.html", user = userInfoCheck, userArticles=userArticlesCheck)
    else:
        flash("Böyle bir kullanıcı yok.","warning")
        return redirect(url_for("indexPage"))

@app.route("/forgot", methods = ["GET", "POST"])
def passwordChangePage():
    form = ResetPassForm(request.form)
    if request.method == "POST":
        logUsername = form.username.data
        userInfoCheck = users.query.filter_by(username=logUsername).first()
        if userInfoCheck:  
            newpass = form.newpass.data
            newpassagain = form.newpassagain.data
            if newpass == newpassagain:
                userInfoCheck.password = sha256_crypt.encrypt(form.newpass.data)
                db.session.commit()
                flash("Şifreniz başarıyla değiştirildi!","success")
    return render_template("forgot.html", form=form)

@app.route("/articles") 
@login_required 
def articlesPage():
    articlesData = articles.query.filter().all()
    if articlesData:
        return render_template("articles.html", articles=articlesData)
    else:
        flash("Bu blogda henüz makale yok.","warning")
        return redirect(url_for("indexPage"))


@app.route("/search", methods=["GET","POST"])
def articleSearch():
    if request.method == "GET":
        return redirect(url_for("indexPage"))
    else:
        keyword = request.form.get("searchKeyword")
        searchWord = "%{}%".format(keyword)
        articleCheck = articles.query.filter(articles.title.like(searchWord))
        if articleCheck:
            return render_template("articles.html", articles=articleCheck)
        else:
            flash("Aranan kelimeyi içeren bir makale bulunamadı.", "warning")
            return redirect(url_for("articlesPage"))

@app.route("/articles/<string:id>")
@login_required 
def articleDetail(id):
    getArticle = articles.query.filter_by(artID = id).first()
    if getArticle:
        return render_template("article.html", article = getArticle)
    else:
        return render_template("article.html")
        

@app.route("/dashboard")
@login_required 
def dashboardPage():    
    articlesData = articles.query.filter().all()
    if articlesData:
        return render_template("dashboard.html", articles=articlesData)
    else:
        return render_template("dashboard.html")

@app.route("/addarticle", methods = ["GET","POST"])
@login_required
def addArticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        regTitle = form.title.data
        regContent = form.content.data
        articleInfo = articles(title = regTitle, content = regContent, author=session["username"])
        db.session.add(articleInfo)
        db.session.commit()
        flash("Makale başarıyla eklendi!","success")
        return redirect(url_for("dashboardPage"))
    else:
        pass
    
    return render_template("addarticle.html", form = form)

@app.route("/delete/<string:id>")
@login_required
def deleteArticle(id):
    getArticle = articles.query.filter_by(artID=id, author = session["username"]).first()
    if getArticle:
        db.session.delete(getArticle)
        db.session.commit()
        flash("Makale başarıyla silindi!","success")
        return redirect(url_for("dashboardPage"))
    else:
        flash("Böyle bir makale yok ya da makale size ait değil!","danger")
        return redirect(url_for("dashboardPage"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, host="192.168.1.33")