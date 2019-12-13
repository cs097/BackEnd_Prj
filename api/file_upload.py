import os

from flask		import Flask, request
from werkzeug.utils	import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './profile_pictures'

@app.route('/profile-picture', methods=['POST'])
def upload_profile_picture():
    if 'profile_pic' not in request.files:
        return 'File is missing', 404

    profile_pic = request.files['profile_pic']

    if profile_pic.filename == '':
        return 'File is missing', 404

    filename = secure_filename(profile_pic.filename)
    profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return '' 200
