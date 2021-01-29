from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import datetime
from functools import wraps
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////blog_directory/blog.db'
app.secret_key = "SECRET_KEY"
db = SQLAlchemy(app)

#Database tables
#user table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
    username = db.Column(db.String)
    password = db.Column(db.String)
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    authorizationGroup = db.Column(db.Integer, default = 1)
    last_activity = db.Column(db.DateTime)
    register_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
# Articles table
class articles(db.Model):
    artID = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String)
    author = db.Column(db.String)
    content = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
# Message table
class messages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    from_id = db.Column(db.Integer, nullable=False)
    to_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String, nullable=False)
    sent_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
# User Permissions Table
class permissions(db.Model):
    groupID = db.Column(db.Integer, primary_key=True)
    groupName = db.Column(db.String)
    canSeePublicContents = db.Column(db.Boolean, default = True)
    canSeePrivateContents = db.Column(db.Boolean, default = False)
    canEditAllContents = db.Column(db.Boolean, default = False)
    canSeeAllUsers = db.Column(db.Boolean, default = True)
    canEditUsers = db.Column(db.Boolean, default = False)
    canDeleteUsers = db.Column(db.Boolean, default = False)
    canAddComment = db.Column(db.Boolean, default = True)
    canSeeAllComments = db.Column(db.Boolean, default = True)
    canSendMessages = db.Column(db.Boolean, default = True)
    canRecieveMessages = db.Column(db.Boolean, default = False)
    canSeeAdminComments = db.Column(db.Boolean, default = False)
    canSeeAdminContents = db.Column(db.Boolean, default = False)
    fullAccess = db.Column(db.Boolean, default = False)
    
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

#Role check decorator
def role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        userInfoCheck = User.query.filter_by(username=session["username"]).first()
        if userInfoCheck.authorizationGroup == 9:
            return f(*args, **kwargs)
        else:
            flash("Bu işlem için yetkiniz bulunmamaktadır!","danger")
            return redirect(url_for("indexPage"))
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
    oldpass = PasswordField("Eski Parola")
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
    content = TextAreaField("Makale İçeriği", validators = [validators.Length(min=20)] )
    

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
        userInfoCheck = User.query.filter_by(username=regUsername).first()
        if userInfoCheck:
            flash("Belirtilen kullanıcı adı mevcut!","danger")
        else:
            regPass = sha256_crypt.encrypt(form.password.data)
            regMail = form.email.data
            regDate = datetime.datetime.now()
            registerSQL = User(username = regUsername, password = regPass, email = regMail, last_activity = regDate, register_date = regDate)
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
        userInfoCheck = User.query.filter_by(username=logUsername).first()
        if userInfoCheck:
            if sha256_crypt.verify(password_ent, userInfoCheck.password):
                flash("Başarıyla giriş yapıldı!","success")
                session["logged_in"] = True       
                session["username"] = logUsername
                currentdate = datetime.datetime.now()
                userInfoCheck.last_activity = currentdate
                userInfoCheck.is_active = True
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
    userInfoCheck = User.query.filter_by(username=session["username"]).first()
    currentdate = datetime.datetime.now()
    userInfoCheck.last_activity = currentdate
    userInfoCheck.is_active = False
    db.session.commit()
    session.clear()
    flash("Başarıyla çıkış yapıldı.","success")
    return redirect(url_for("indexPage"))

@app.route("/user/<string:username>")
@login_required
def userProfile(username):
    userInfoCheck = User.query.filter_by(username=username).first()
    selfInfoCheck = User.query.filter_by(username=session["username"]).first()
    if userInfoCheck:
        userArticlesCheck = articles.query.filter_by(author=userInfoCheck.username).all()
        return render_template("user.html", user = userInfoCheck, userArticles=userArticlesCheck, selfinfo = selfInfoCheck)
    else:
        flash("Böyle bir kullanıcı yok.","warning")
        return redirect(url_for("indexPage"))

@app.route("/forgot", methods = ["GET", "POST"])
def passwordChangePage():
    form = ResetPassForm(request.form)
    if request.method == "POST":
        logUsername = form.username.data
        userInfoCheck = User.query.filter_by(username=logUsername).first()
        if userInfoCheck:
            oldpass = form.oldpass.data  
            newpass = form.newpass.data
            newpassagain = form.newpassagain.data
            if sha256_crypt.verify(oldpass, userInfoCheck.password):
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

@app.route("/userdashboard")
@login_required 
def userdashboardPage():    
    articlesData = articles.query.filter_by(author = session["username"]).all()
    if articlesData:
        return render_template("userdashboard.html", articles=articlesData)
    else:
        return render_template("userdashboard.html")

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

@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        getArticle = articles.query.filter_by(artID=id, author = session["username"]).first()
        if getArticle:
            form = ArticleForm()
            form.title.data = getArticle.title
            form.content.data = getArticle.content
            return render_template("editarticle.html",form = form)
        else:
            flash("Böyle bir makale yok ya da makale size ait değil!","danger")
            return redirect(url_for("dashboardPage"))
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        getArticle = articles.query.filter_by(artID=id, author = session["username"]).first()
        getArticle.title = newTitle
        getArticle.content = newContent
        db.session.commit()
        flash("Makale başarıyla güncellendi!","success")
    return redirect(url_for("dashboardPage"))

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
    app.run(debug=True)
