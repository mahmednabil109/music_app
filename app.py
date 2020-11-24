#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import logging
import sys
import json, dateutil.parser, babel
from datetime import datetime
from flask import (Flask, render_template, request, Response, flash, redirect, url_for)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging import Formatter, FileHandler
from werkzeug.urls import url_encode
from flask_wtf import Form
from forms import *
from models import (app, db, migrate, Artist, Venue, Show)


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app.config.from_object('config')
moment = Moment(app)
db.init_app(app)

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

def get_venues_by_cities():
  data = []
  venues = Venue.query.all()
  cities = Venue.query.distinct(Venue.city,Venue.state).all()
  for place in cities:
    data.append({
      'city' : place.city,
      'state' : place.state,
      'venues':[{
          'id' : venue.id,
          'name' : venue.name,
          'num_upcoming_shows' : db.session.query(Show).filter(Show.venue_id == venue.id,Show.start_time >= datetime.now()).count()
      }
      for venue in venues if venue.city == place.city and venue.state == place.state
      ]
    })
  return data

@app.route('/venues')
def venues():
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data = get_venues_by_cities()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_key = request.form.get("search_term","")
  search_res = db.session.query(Venue.id,Venue.name).filter(Venue.name.ilike("%{}%".format(search_key))).all()
  venues = [{
    'id' : venue.id,
    'name' : venue.name,
    'num_upcoming_shows' : db.session.query(Show).filter(Show.venue_id == venue.id,Show.start_time >= datetime.now()).count()
  }
    for venue in search_res
  ]
  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  db_venue = Venue.query.filter_by(id = venue_id).first_or_404()

  upcoming_shows = db.session.query(Artist,Show).join(Show).join(Venue).\
                   filter(Show.venue_id == venue_id,
                          Show.artist_id == Artist.id,
                          Show.start_time >= datetime.now()).all()
  past_shows  = db.session.query(Artist,Show).join(Show).join(Venue).\
                filter(Show.venue_id == venue_id,
                      Show.artist_id == Artist.id,
                      Show.start_time < datetime.now()).all()

  data = {
    "id": db_venue.id,
    "name": db_venue.name,
    "genres": list(db_venue.geners.split(',')),
    "city": db_venue.city,
    "state": db_venue.state,
    "phone": db_venue.phone,
    "seeking_talent": bool(db_venue.seeking_talent),
    "past_shows": [{
      "artist_id" : artist.id,
      "artist_name" : artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
      for artist,show in past_shows ],
    "upcoming_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist,show in upcoming_shows],
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
    print(sys.exc_info())
    error = True
    db.session.rollback()

  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('Venue ' + request.form['name'] + ' was not listed! there is a problem!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    db_venue = Venue.query.get(int(venue_id))
    if not db_venue:
      raise Exception()
    db.session.delete(db_venue)
    db.session.commit()
  except:
    print(sys.exc_info())
    error = True
    db.session.rollback()
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'), code = 200)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  db_artists = db.session.query(Artist.id,Artist.name).all()
  data=[]
  for artist in db_artists:
    data.append({"id":artist[0],"name":artist[1]})
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_key = request.form.get("search_term","")
  search_res = db.session.query(Artist.id,Artist.name).filter(Artist.name.ilike("%{}%".format(search_key))).all()
  artists = [{
    'id' : artist.id,
    'name' : artist.name,
    'num_upcoming_shows' : db.session.query(Show.id).filter(Show.artist_id == artist.id,Show.start_time >= datetime.now()).count()
  }
    for artist in search_res
  ]
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  db_artist = Artist.query.filter_by(id = artist_id).first_or_404()

  upcoming_shows = db.session.query(Venue,Show).join(Show).join(Artist).\
                              filter(
                                Show.artist_id == artist_id,
                                Show.venue_id == Venue.id,
                                Show.start_time >= datetime.now()
                              ).all()
  past_shows = db.session.query(Venue,Show).join(Show).join(Artist).\
                              filter(
                                Show.artist_id == artist_id,
                                Show.venue_id == Venue.id,
                                Show.start_time < datetime.now()
                              ).all()

  data = {
    "id": db_artist.id,
    "name": db_artist.name,
    "genres": list(db_artist.genres.split(',')),
    "city": db_artist.city,
    "state": db_artist.state,
    "phone": db_artist.phone,
    "seeking_venue": bool(db_artist.seeking_venue),
    "past_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for venue,show in past_shows ],
    "upcoming_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for venue,show in upcoming_shows],
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
    print(sys.exc_info())
    pass;
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes
  error = False
  data = request.form
  try:
    artist = Artist.query.get(int(artist_id))
    if not artist:
      raise Exception()
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
    print(sys.exc_info())
    error = True
    db.session.rollback()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  db_venue = Venue.query.get(int(venue_id))
  venue = {}
  error = False
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
  except:
    print(sys.exc_info())
    pass;
  # venue record with ID <venue_id> using the new attributes
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  data = request.form
  try:
    venue = Venue.query.get(int(venue_id))
    if not venue:
      raise Exception()
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
    print(sys.exc_info())
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
    print(sys.exc_info())
    error = True
    db.session.rollback()

  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
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
  shows = db.session.query(Artist,Show,Venue).join(Show,Artist.id == Show.artist_id).join(Venue , Venue.id == Show.venue_id).all()
  print(shows) 
  data = [{
    "venue_id": venue.id,
    "venue_name": venue.name,
    "artist_id": artist.id,
    "artist_name": artist.name,
    "artist_image_link": artist.image_link,
    "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  }
    for artist,show,venue in shows ]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  data = request.form
  try:
    show = Show(artist_id = data.get('artist_id'),
                venue_id = data.get('venue_id'),
                start_time = data.get('start_time'))
    db.session.add(show)
    db.session.commit()
  except:
    print(sys.exc_info())
    error = True
    db.session.rollback()
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    flash('Show was not listed! due to an Error(s)!')

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
