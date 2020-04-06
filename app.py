#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate =Migrate(app,db)
# TODO: connect to a local postgresql database

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
    image_link = db.Column(db.String(500))
    genres=db.Column(db.ARRAY(db.String),nullable=False)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)
    
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
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
    venues_list = Venue.query.order_by(Venue.city, Venue.state).all()
    data = []
    city_state = ''
    for venue in venues_list:
        #inner join and count where Venue.id==this event.id
        num_upcoming_shows = db.session.query(Venue).join(Show).filter(Venue.id == venue.id, Show.start_time > datetime.now()).count()
        
        if city_state == '' or venue.city+venue.state!=city_state:
            data.append({
                'city': venue.city,
                'state': venue.state,
                'venues': [{
                    'id': venue.id,
                    'name': venue.name
                }]
            })
            city_state = venue.city + venue.state
        else:
            data[len(data) - 1]['venues'].append({
                'id': venue.id,
                'name': venue.name
            })
            
    return render_template('pages/venues.html', areas=data)
@app.route('/venues/search', methods=['POST'])
def search_venues():
  result={}
  try:
    venue_list=Venue.query.with_entities(Venue.id,Venue.name).filter(Venue.name.ilike('%'+request.form.get('search_term','')+'%')).all()
    result['data']=venue_list
    result['count']=len(venue_list)
  except Exception as e:
    print(e)
    flash('An error occured for search')
  finally:
    return render_template('pages/search_venues.html', results=result, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    setattr(venue, 'past_shows', [])
    setattr(venue, 'upcoming_shows', [])
    current_time = datetime.now()
    past_shows_count = 0
    upcoming_shows_count = 0
    shows = db.session.query(Artist, Show.start_time).join(Show).filter(Show.venue_id == venue_id)
    for artist, start_time in shows:
        if start_time < current_time:
            venue.past_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(start_time)
            })
            past_shows_count += 1
        else:
            venue.upcoming_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(start_time)
            })
            upcoming_shows_count += 1
    setattr(venue, 'past_shows_count', past_shows_count)
    setattr(venue, 'upcoming_shows_count', upcoming_shows_count)
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    error = False
    try:
        if form.validate_on_submit():
            venue = Venue(
                name=form.name.data,city=form.city.data,state=form.state.data,phone=form.phone.data,
                address=form.address.data,genres=form.genres.data,image_link=form.image_link.data,
                website=form.website.data,facebook_link=form.facebook_link.data,
                seeking_talent=form.seeking_talent.data,seeking_description=form.seeking_description.data
            )
            db.session.add(venue)
            db.session.commit()
            # TODO: insert form data as a new Venue record in the db, instead
            # TODO: modify data to be the data object returned from db
            # insertion
        else:
            raise Exception('Form validation Failed')
    except Exception as e:
        print('create_venue_submission: ', e)
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
        # on successful db insert, flash success
    if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be
        # listed.')
        flash('An error occurred. Venue '+request.form['name']+' could not be listed.')
        return render_template('forms/new_venue.html', form=form)
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
    response = {}
    try:
        artist_list = Artist.query.with_entities(Artist.id, Artist.name).\
            filter(Artist.name.ilike('%' + request.form.get('search_term', '')
                                     + '%')).all()
        response['data'] = artist_list
        response['count'] = len(artist_list)
    except Exception as e:
        print(e)
        flash('An error occurred for the search term' +
              request.form.get('search_term', ''))
    finally:
        return render_template('pages/search_artists.html', results=response,
                               search_term=request.form.get('search_term', ''))
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    current_time = datetime.now()
    artist = Artist.query.get(artist_id)
    setattr(artist, 'past_shows', [])
    setattr(artist, 'upcoming_shows', [])
    past_shows_count = 0
    upcoming_shows_count = 0
    shows = db.session.query(Venue, Show.start_time).join(Show).filter(Show.artist_id == artist_id)
    for venue, start_time in shows:
        if start_time < current_time:
            artist.past_shows.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(start_time)
            })
            past_shows_count += 1
        else:
            artist.upcoming_shows.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(start_time)
            })
            upcoming_shows_count += 1
    setattr(artist, 'past_shows_count', past_shows_count)
    setattr(artist, 'upcoming_shows_count', upcoming_shows_count)

    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(
        name=artist.name,
        genres=artist.genres,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        website=artist.website,
        facebook_link=artist.facebook_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        image_link=artist.image_link
    )
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm()
    error = False
    try:
        if form.validate_on_submit():
            artist.name = form.name.data
            artist.genres = form.genres.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.website = form.website.data
            artist.facebook_link = form.facebook_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.image_link = form.image_link.data
            db.session.add(artist)
            db.session.commit()
        else:
            raise Exception('Form validation failed')
    except Exception as e:
        print('edit_artist_submission: ', e)
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
        return render_template('forms/edit_artist.html', form=form, artist=artist)
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  #get row from database and create form and fill with same data
  form = VenueForm(
      name=venue.name,
      genres=venue.genres,
      address=venue.address,
      city=venue.city,
      state=venue.state,
      phone=venue.phone,
      website=venue.website,
      facebook_link=venue.facebook_link,
      seeking_talent=venue.seeking_talent,
      seeking_description=venue.seeking_description,
      image_link=venue.image_link,
  )
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    form = VenueForm()
    error = False
    try:
        if form.validate_on_submit():
            venue.name = form.name.data
            venue.genres = form.genres.data
            venue.address = form.address.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.phone = form.phone.data
            venue.website = form.website.data
            venue.facebook_link = form.facebook_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.image_link = form.image_link.data
            db.session.add(venue)
            db.session.commit()
        else:
            raise Exception('Form validation failed')
    except Exception as e:
        print('edit_venue_submission: ', e)
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
        return render_template('forms/edit_venue.html', form=form, venue=venue)
    else:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error = False
    print(form.name)
    try:
        if form.validate_on_submit():
            print('Did i enter validation?')
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(artist)
            db.session.commit()
        else:
            raise Exception('Form validation failed')
    except Exception as e:
        print('create_artist_submission: ', e)
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] +
              ' could not be listed.')
        return render_template('forms/new_artist.html', form=form)
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    #inner join on three tables get all attributes associated to each table
    shows = db.session.query(Show, Venue.name, Artist).join(Venue, Artist)
    for show, venue_name, artist in shows:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': venue_name,
            'artist_id': show.artist_id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start_time)
        })
        print('data: ', data[0]['start_time'])
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    print(form.csrf_token)
    error = False
    try:
        print('Form Validated')
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
    except Exception as e:
        print('create_show_submission: ', e)
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_show.html', form=form)
    else:
        flash('Show was successfully listed!')
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
