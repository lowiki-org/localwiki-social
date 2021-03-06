from flask import Flask, request, render_template, flash, redirect
from flask_uploads import UploadSet, IMAGES, patch_request_class, configure_uploads
from flask_bootstrap import Bootstrap

from twitter import Twitter, OAuth, TwitterError
from user_agents import parse

import os

app = Flask(__name__)
app.config.from_pyfile('localsettings.cfg')
Bootstrap(app)
photos = UploadSet('photos', IMAGES)
configure_uploads(app, (photos,))
# Limit image size
patch_request_class(app, 5 * 1024 * 1024)


@app.route("/", methods=['POST', 'GET'])
def add():
    if request.method == 'GET':
        if not request.args.get('debug', ''):
            ua_string = request.headers.get('User-Agent')
            user_agent = parse(ua_string)
            if user_agent.is_pc : return redirect('https://lowiki.tw')

    elif request.method == 'POST' and request.form['message']:
        m = request.form['message']
        l = []
        for name in ('image-1', 'image-2', 'image-3', 'image-4'):
            image = request.files[name]
            if image:
                l.append(photos.save(image))

        e, mp = post_to_twitter(m,
                                l,
                                request.form['region'],
                                request.form['lat'],
                                request.form['long'])
        if e:
            app.logger.error(e)
            flash(e, 'error')
        else:
            app.logger.info(mp)
            flash(mp)

    return render_template('add.html', region=request.args.get('region', ''))


def post_to_twitter(message, file_list, hashtag="", lat=None, lng=None):
    auth = OAuth(app.config['TOKEN'],
                 app.config['TOKEN_KEY'],
                 app.config['CON_SECRET'],
                 app.config['CON_SECRET_KEY'])

    t = Twitter(auth=auth)
    t_upload = Twitter(domain='upload.twitter.com', auth=auth)

    image_list = []
    for filename in file_list:
        path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
        with open (path, "rb") as imagefile:
            image = imagefile.read()
            if image:
                image_id = t_upload.media.upload(media=image)["media_id_string"]
                image_list.append(image_id)

    # Prepare data to post to twitter
    kwargs = {}
    if len(hashtag):
        kwargs['status'] = "%s #%s" % (message, hashtag)
    else:
        kwargs['status'] = message

    if len(image_list):
        kwargs['media_ids'] = ",".join(image_list)
    if lat and lng:
        kwargs['lat'] = float(lat)
        kwargs['long'] = float(lng)
        app.logger.info("Post location %s,%s" % (lat, lng))

    error = None
    response = None
    try:
        r = t.statuses.update(**kwargs)
        response = "Post success"
        app.logger.info("Post id %s" % r['id'])
    except TwitterError as e:
        app.logger.error(e)
        error_message = e.response_data['errors'][0]['message']
        if error_message:
            error = "Error, %s" % error_message
        else:
            error = "Error on post"

    return (error, response)

if __name__ == "__main__":
    log_path = app.config['LOG']
    if log_path:
        import logging
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(log_path, maxBytes=10000, backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    app.run(host=app.config['LISTEN'], port=app.config['PORT'])
