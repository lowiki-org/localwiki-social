from flask import Flask, request, render_template, flash
from flask.ext.uploads import UploadSet, IMAGES, patch_request_class

from twitter import Twitter, OAuth

import os

app = Flask(__name__)


@app.route("/", methods=['POST', 'GET'])
def add():
    return render_template('add.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error = None
    photos = UploadSet(app.config['upload_folder'], IMAGES)
    if request.method == 'POST' and request.message:
        filename = photos.save(request.files['photo'])
        rec = Photo(filename=filename, user=g.user.id)
        rec.store()
        flash("Photo saved.")
        return redirect(url_for('show', id=rec.id))
    return render_template('upload.html', error=error)


def post_to_twitter(message, file_list, coordinates=None):
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

    # "geo": { "type":"Point", "coordinates":[37.78217, -122.40062] }

    if len(image_list):
        r = t.statuses.update(status=message, media_ids=",".join(image_list))
    else:
        r = t.statuses.update(status=message)
    # flash(r)

if __name__ == "__main__":
    app.config.from_pyfile('localsettings.cfg')
    patch_request_class(app, 5 * 1024 * 1024)

    app.run()
