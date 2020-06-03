import os
import uuid

from flask import (
    Blueprint,
    current_app,
    request,
    send_from_directory,
    url_for,
)
from flask.views import MethodView


class ImagesView(MethodView):
    def post(self):
        file = request.files['image']
        upload_dir = current_app.config['UPLOAD_DIR']
        filename = f'{uuid.uuid4()}{os.path.splitext(file.filename)[1]}'
        file.save(os.path.join(upload_dir, filename))
        return {
            'url': url_for('images.download_image', image_name=filename)
        }


class ImageView(MethodView):
    def get(self, image_name):
        upload_dir = current_app.config['UPLOAD_DIR']
        return send_from_directory(upload_dir, image_name)


bp = Blueprint('images', __name__)
bp.add_url_rule('', view_func=ImagesView.as_view('upload_image'))
bp.add_url_rule('/<image_name>', view_func=ImageView.as_view('download_image'))
