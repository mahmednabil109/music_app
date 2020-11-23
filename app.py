#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, dateutil.parser, babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from werkzeug.urls import url_encode
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))

    # pTODO: implement any missing fields, as a database migration using Flask-Migrate
    geners = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean() ,default=False)
    seeking_description = db.Column(db.String(120))
    venue_events = db.relationship('Show',back_populates='venue',lazy=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # pTODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(),default=False)
    seeking_description = db.Column(db.String(120))
    artist_events = db.relationship('Show',back_populates='artist',lazy=True)

# pTODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False)
  venue_id = db.Column(db.Integer ,db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  venue = db.relationship('Venue', back_populates='venue_events')
  artist = db.relationship('Artist', back_populates='artist_events')

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
def get_brief_info_venue(venues):
  res = []
  current = datetime.utcnow()
  for venue in venues:
      upcoming_shows = len([s for s in db.session.query(Show.id,Show.start_time).filter(Show.venue_id == venue[0]) if s[1] >= current]) 
      obj2 = {"id":venue[0],"name":venue[1],"num_upcoming_shows":upcoming_shows}
      res.append(obj2)
  return res
def get_venues_by_cities():
  data = []
  cities = list(set(db.session.query(Venue.city,Venue.state).all()))
  for city in cities:
    obj = {"city":city[0],"state":city[1],"venues":[]}
    venues = list(db.session.query(Venue.id,Venue.name).filter(Venue.city == obj["city"]).filter(Venue.state == obj["state"]).all())
    obj["venues"] = get_brief_info_venue(venues)
    data.append(obj)
  #print(data)
  return data

@app.route('/venues')
def venues():
  # pTODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = get_venues_by_cities()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # pTODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_key = request.form.get("search_term","")
  search_res = db.session.query(Venue.id,Venue.name).filter(Venue.name.ilike("%{}%".format(search_key))).all()
  venues = get_brief_info_venue(search_res)
  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

def get_shows_venue(venue_id):
  shows = db.session.query(Show.artist_id,Show.start_time).filter(Show.venue_id == venue_id).all()
  upcoming,past = [], []
  current = datetime.utcnow()
  for show in shows:
    obj = {"artist_id":show[0],"artist_name":0,"artist_image_link":0,"start_time":str(show[1])}
    tmp_artist = db.session.query(Artist.name,Artist.image_link).filter(Artist.id == show[0]).first()
    obj["artist_name"] = tmp_artist[0]
    obj["artist_image_link"] = tmp_artist[1]
    if(show[1] >= current):
      upcoming.append(obj)
    else:
      past.append(obj)
  return upcoming,past

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # pTODO: replace with real venue data from the venues table, using venue_id
  db_venue = Venue.query.get(int(venue_id))
  if not db_venue:
    flash('Venue with id ' + str(venue_id) + ' dose not exist!')
    return redirect(url_for('index'))

  upcoming_shows,past_shows = get_shows_venue(venue_id)
  data={
    "id": db_venue.id,
    "name": db_venue.name,
    "genres": list(db_venue.geners.split(',')),
    "city": db_venue.city,
    "state": db_venue.state,
    "phone": db_venue.phone,
    "seeking_talent": bool(db_venue.seeking_talent),
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  if db_venue.address :
    data['address'] = db_venue.address
  if db_venue.facebook_link :
    data['facebook_link'] = db_venue.facebook_link
  if db_venue.image_link :
    data['image_link'] = db_venue.image_link
  if db_venue.website_link :
    data['website'] = db_venue.website_link
  if db_venue.seeking_talent:
    data['seeking_description'] = db_venue.seeking_description
 
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # pTODO: insert form data as a new Venue record in the db, instead
  # pTODO: modify data to be the data object returned from db insertion
  error = False
  data = request.form
  try:
    venue = Venue(name = data.get('name'),
                  city = data.get('city'),
                  state = data.get('state'),
                  address = data.get('address'),
                  phone = data.get('phone'),
                  facebook_link = data.get('facebook_link'),
                  image_link = data.get('image_link'),
                  website_link = data.get('website_link'),
                  geners = ','.join(data.getlist('genres')),
                  seeking_talent = (data.get('seeking') == 'on'),
                  seeking_description = data.get('seeking_des')
                  )
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    pass    
  # on successful db insert, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    # pTODO: on unsuccessful db insert, flash an error instead.
    flash('Venue ' + request.form['name'] + ' was not listed! there is a problem!')

  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # PTODO: Complete this endpoint for taking a venue_id, and using
  error = False
  try:
    db_venue = Venue.query.get(int(venue_id))
    if not db_venue:
      raise Exception()
    db.session.delete(db_venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # PTODO: BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'), code = 200)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # pTODO: replace with real data returned from querying the database
  db_artists = db.session.query(Artist.id,Artist.name).all()
  data=[]
  for artist in db_artists:
    data.append({"id":artist[0],"name":artist[1]})
  return render_template('pages/artists.html', artists=data)


def get_brief_info_artist(artists):
  res = []
  current = datetime.utcnow()
  for artist in artists:
    obj = {"id": artist[0],"name":artist[1],"num_upcoming_shows":0}
    num = len([s for s in db.session.query(Show.id,Show.start_time) if s[1] >= current])
    obj["num_upcoming_shows"] = num
    res.append(obj)
  return res

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # pTODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_key = request.form.get("search_term","")
  search_res = db.session.query(Artist.id,Artist.name).filter(Artist.name.ilike("%{}%".format(search_key)))
  artists = get_brief_info_artist(search_res)
  print(artists)
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

def get_shows_artist(artist_id):
  shows = db.session.query(Show.venue_id,Show.start_time).filter(Show.artist_id == artist_id).all()
  upcoming,past = [], []
  current = datetime.utcnow()
  for show in shows:
    obj = {"venue_id":show[0],"venue_name":0,"venue_image_link":0,"start_time":str(show[1])}
    tmp_venue = db.session.query(Venue.name,Venue.image_link).filter(Venue.id == show[0]).first()
    obj["venue_name"] = tmp_venue[0]
    obj["venue_image_link"] = tmp_venue[1]
    if(show[1] >= current):
      upcoming.append(obj)
    else:
      past.append(obj)
  return upcoming,past

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # pTODO: replace with real venue data from the venues table, using venue_id
  db_artist = Artist.query.get(int(artist_id))
  if not db_artist:
    flash('Artist with id ' + str(artist_id) + ' dose not exist!')
    return redirect(url_for('index'))
  upcoming_shows,past_shows = get_shows_artist(artist_id)
  data = {
    "id": db_artist.id,
    "name": db_artist.name,
    "genres": list(db_artist.genres.split(',')),
    "city": db_artist.city,
    "state": db_artist.state,
    "phone": db_artist.phone,
    "seeking_venue": bool(db_artist.seeking_venue),
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
 
  if db_artist.facebook_link :
    data['facebook_link'] = db_artist.facebook_link
  if db_artist.image_link :
    data['image_link'] = db_artist.image_link
  if db_artist.website_link :
    data['website'] = db_artist.website_link
  if db_artist.seeking_venue:
    data['seeking_description'] = db_artist.seeking_description
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  db_artist = Artist.query.get(int(artist_id))
  artist = {}

  try:
    if not db_artist :
      raise Exception()
    artist={
      "id": db_artist.id,
      "name": db_artist.name,
      "genres": list(db_artist.genres.split(',')),
      "city": db_artist.city,
      "state": db_artist.state,
      "phone": db_artist.phone,
      "website": db_artist.website_link,
      "facebook_link": db_artist.facebook_link,
      "seeking_venue": bool(db_artist.seeking_venue),
      "seeking_description":  db_artist.seeking_description,
      "image_link": db_artist.image_link
    }
  except:
    pass;
  # TPODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # pTODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  data = request.form
  try:
    print(int(venue_id))
    artist = Artist.query.get(int(artist_id))
    if not artist:
      raise Exception()
    print(venue)
    artist.name = data.get('name')
    artist.city = data.get('city')
    artist.state = data.get('state')
    artist.phone = data.get('phone')
    artist.facebook_link = data.get('facebook_link')
    artist.image_link = data.get('image_link')
    artist.website_link = data.get('website_link')
    artist.geners = ','.join(data.getlist('genres'))
    artist.seeking_description = data.get('seeking_des')
    artist.seeking_venue = (data.get('seeking') == 'on')
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  db_venue = Venue.query.get(int(venue_id))
  venue = {}
  error = False
  # pTODO: populate form with values from venue with ID <venue_id>
  try:
    if not db_venue :
      raise Exception()
    venue = {
      "id": venue_id,
      "name":db_venue.name,
      "genres": list(db_venue.geners.split(',')),
      "address": db_venue.address,
      "city": db_venue.city,
      "state": db_venue.state,
      "phone": db_venue.phone,
      "website": db_venue.website_link,
      "facebook_link": db_venue.facebook_link,
      "seeking_talent": bool(db_venue.seeking_talent),
      "seeking_description": db_venue.seeking_description,
      "image_link": db_venue.image_link
    }
    print(venue)
  except:
    pass;
  # venue record with ID <venue_id> using the new attributes
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # pTODO: take values from the form submitted, and update existing
  error = False
  data = request.form
  try:
    print(int(venue_id))
    venue = Venue.query.get(int(venue_id))
    if not venue:
      raise Exception()
    print(venue)
    venue.name = data.get('name')
    venue.city = data.get('city')
    venue.state = data.get('state')
    venue.address = data.get('address')
    venue.phone = data.get('phone')
    venue.facebook_link = data.get('facebook_link')
    venue.image_link = data.get('image_link')
    venue.website_link = data.get('website_link')
    venue.geners = ','.join(data.getlist('genres'))
    venue.seeking_talent = (data.get('seeking') == 'on')
    venue.seeking_description = data.get('seeking_des')
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    pass    
  # on successful db modification, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    # on unsuccessful db insert, flash an error instead.
    flash('Venue ' + request.form['name'] + ' was not listed! there is a problem!')
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  data = request.form
  try:
    # pTODO: insert form data as a new Venue record in the db, instead
    # pTODO: modify data to be the data object returned from db insertion
    artist = Artist(name = data.get('name'),
                    city = data.get('city'),
                    state = data.get('state'),
                    phone = data.get('phone'),
                    genres = ','.join(data.getlist('genres')),
                    facebook_link = data.get('facebook_link'),
                    image_link = data.get('image_link'),
                    website_link = data.get('website_link'),
                    seeking_venue = (data.get('seeking') == 'on'),
                    seeking_description = data.get('seeking_des'))
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()

  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    # pTODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('Artist ' + request.form['name'] + ' was not listed! due to some error(s)')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
def get_brief_info_show(shows):
  res = []
  for show in shows:
    artist = db.session.query(Artist.name,Artist.image_link).filter(Artist.id == show[1]).first()
    venue = db.session.query(Venue.name).filter(Venue.id == show[0]).first()
    obj = {
    "venue_id": show[0],
    "venue_name": venue[0],
    "artist_id": show[1],
    "artist_name": artist[0],
    "artist_image_link": artist[1],
    "start_time": str(show[2])
    }
    res.append(obj)
  return res

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # pTODO: replace with real venues data.
  shows = db.session.query(Show.venue_id,Show.artist_id,Show.start_time).all()
  data = get_brief_info_show(shows)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # pTODO: insert form data as a new Show record in the db, instead
  error = False
  data = request.form
  try:
    show = Show(artist_id = data.get('artist_id'),
                venue_id = data.get('venue_id'),
                start_time = data.get('start_time'))
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    # PTODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    flash('Show was not listed! due to an Error(s)!')

  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
