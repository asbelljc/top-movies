import os
import requests

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
Bootstrap(app)

# Create database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Create table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


# Rating form
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10, e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


# New movie form
class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])


@app.route("/")
def home():
    all_movies = Movie.query.all()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()

    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": API_KEY, "query": movie_title},
        )
        data = response.json()["results"]

        return render_template("select.html", options=data)

    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(
            movie_api_url, params={"api_key": API_KEY, "language": "en-US"}
        )
        data = response.json()
        print(
            f"https://api.themoviedb.org/3/movie/{movie_api_id}/images{data['poster_path']}"
        )
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/original{data['poster_path']}",
            description=data["overview"],
        )

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == "__main__":
    app.run(debug=True)
