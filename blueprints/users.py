import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    session
)
from flask.views import MethodView
from database import db
from services.users import UsersService,CitiesService

bp = Blueprint('users', __name__)


class UsersView(MethodView):

    def post(self):
        request_json = request.json
        email = request_json.get('email')
        password = request_json.get('password')
        first_name = request_json.get('first_name')
        last_name = request_json.get('last_name')
        is_seller = request_json.get('is_seller')

        if is_seller:
            phone = request_json.get('phone')
            zip_code = int(request_json.get('zip_code'))
            city_id = int(request_json.get('city_id'))
            street = request_json.get('street')
            home = request_json.get('home')

        with db.connection as con:
            service = UsersService(con)
            acc_id = service.create_account(first_name, last_name, email, password)
            try:
                if is_seller:
                    CitiesService(con).create_zip_code(
                        zip_code=zip_code,
                        city_id=city_id
                    )
                    service.create_seller(acc_id, phone, zip_code, street, home)
                con.commit()
            except sqlite3.IntegrityError:
                return '', 409

        resp = service.get_user(acc_id, is_seller)
        return jsonify(resp),200


class UserView(MethodView):
    def get(self, account_id):
        if not session.get('user_id', ):
            return '', 401
        with db.connection as con:
            service = UsersService(con)
            is_seller = service.account_is_seller(account_id)
            account = service.get_user(account_id, is_seller)
            if not account:
                return '', 404
        return jsonify(account), 200

    def patch(self, account_id):
        def update_data(data_dict, key, req_json):
            if req_json.get(key):
                data_dict.update({key: req_json[key]})
            return data_dict

        if not session.get('user_id'):
            return '', 401

        if account_id != session['user_id']:
            return '', 403

        request_json = request.json
        with db.connection as con:
            service = UsersService(con)
            acc_update = dict()
            update_data(acc_update, 'first_name', request_json)
            update_data(acc_update, 'last_name', request_json)
            service.update_account(account_id, acc_update)
            is_seller_update = request_json.get('is_seller')
            is_seller = service.account_is_seller(account_id)

            if is_seller_update is not None:

                if is_seller_update is True:

                    seller_update = dict()
                    zipcode_update = dict()
                    update_data(seller_update, 'phone', request_json)
                    update_data(seller_update, "zip_code", request_json)
                    update_data(seller_update, "street", request_json)
                    update_data(seller_update, "home", request_json)
                    update_data(zipcode_update, "zip_code", request_json)
                    update_data(zipcode_update, "city_id", request_json)

                    CitiesService(con).create_zip_code(
                        zip_code=zipcode_update['zip_code'],
                        city_id=zipcode_update['city_id']
                    )
                    if is_seller is False:
                        service.create_seller(
                            account_id=account_id,
                            zip_code=zipcode_update['zip_code'],
                            home=seller_update['home'],
                            phone=seller_update['phone'],
                            street=seller_update['street']
                        )
                        user = service.get_user(account_id, is_seller_update)
                        return jsonify(user), 200
                    else:
                        service.update_seller(account_id, seller_update)
                        return jsonify(UsersService(con).get_user(account_id, is_seller_update)), 200
                else:
                    if is_seller is True:
                        with db.connection as con:
                            cur = con.execute(
                                f'SELECT * '
                                f'FROM ad '
                                f'WHERE seller_id = {account_id} '
                            )
                            ads = [dict(row) for row in cur.fetchall()]
                            for ad in ads:
                                car_id = ad['car_id']
                                con.execute(
                                    f'DELETE FROM carcolor '
                                    f'WHERE car_id = {car_id}'
                                )
                                con.execute(
                                    f'DELETE FROM car '
                                    f'WHERE id = {car_id}'
                                )
                                con.execute(
                                    f'DELETE FROM image '
                                    f'WHERE car_id = {car_id}'
                                )
                                con.execute(
                                    f'DELETE FROM ad '
                                    f'WHERE seller_id = {account_id} '
                                )
                                con.execute(
                                    f'DELETE FROM seller '
                                    f'WHERE account_id = {account_id}'
                                )
            is_seller_update = is_seller
            result = jsonify(UsersService(con).get_user(account_id, is_seller_update))
            return result, 200


bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('/<int:account_id>', view_func=UserView.as_view('user'))
