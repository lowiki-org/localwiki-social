from flask import Flask, request, render_template
from flask.ext.uploads import UploadSet

from twitter import *


app = Flask(__name__)
app.config.from_object('local.settings')
photos = UploadSet(app.config['upload_folder'])


@app.route("/", methods=['POST', 'GET'])
def add():
    error = None
    if request.method == 'POST' and request.message:
        request.form['']
    return render_template('add.html', error=error)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        rec = Photo(filename=filename, user=g.user.id)
        rec.store()
        flash("Photo saved.")
        return redirect(url_for('show', id=rec.id))
    return render_template('upload.html')


def post_to_twitter(file_list):
    auth = OAuth(app.config['token'],
                 app.config['token_key'],
                 app.config['con_secret'],
                 app.config['con_secret_key'])

    t = Twitter(auth=auth)
    t_upload = Twitter(domain='upload.twitter.com', auth=auth)
    image_list = []

    for filename in file_list:
        with open (filename, "rb") as imagefile:
            image = imagefile.read()
            if image:
                image_id = t_upload.media.upload(media=image)["media_id_string"]
                image_list.append(image_id)

    t.statuses.update(status=message, media_ids=",".join(image_list))


if __name__ == "__main__":
    app.run()
