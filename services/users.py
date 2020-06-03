from werkzeug.security import generate_password_hash


class UsersService:
	def __init__(self, connection):
		self.connection = connection

	def create_account(self, first_name, last_name, email, password):
		password_hash = generate_password_hash(password)
		try:
			cur = self.connection.execute(
				f'INSERT INTO account (first_name, last_name, email, password)'
				f'VALUES ("{first_name}", "{last_name}", "{email}", "{password_hash}")'
			)
		except:
			return None
		print(cur.lastrowid)
		account_id = cur.lastrowid
		return account_id

	def create_seller(self, account_id, phone, zip_code, street, home):
		self.connection.execute(
			f'INSERT INTO seller (zip_code, street, home, phone, account_id)'
			f'VALUES ({zip_code}, "{street}", "{home}", "{phone}", {account_id})'
		)

	def get_user(self, user_id, is_seller):
		SELECT = 'SELECT account.id, email, first_name, last_name '
		FROM = 'FROM account '
		if is_seller:
			SELECT += ',seller.zip_code, street, home, phone, city_id '
			FROM += 'JOIN seller ON account.id = seller.account_id ' \
			        'JOIN zipcode ON zipcode.zip_code = seller.zip_code '
		cur = self.connection.execute(
			f'{SELECT}'
			f'{FROM}'
			f'WHERE account.id = {user_id}'
		)
		try:
			user = dict(cur.fetchone())
		except:
			return None
		user.update({'is_seller': is_seller})
		return user

	def account_is_seller(self, account_id):
		cur = self.connection.execute(
			f'SELECT * '
			f'FROM seller '
			f'WHERE account_id = {account_id}'
		)
		row = cur.fetchone()
		if row:
			return True
		return False

	def update_account(self, account_id, update_account_data):
		set_params = ', '.join(f'{key} = "{val}"' for key, val in update_account_data.items())
		self.connection.execute(
			f'UPDATE account '
			f'SET {set_params}'
			f'WHERE id = {account_id} '
		)

	def update_seller(self, account_id, update_seller_data):
		set_params = ', '.join(f'{key} = "{val}"' for key, val in update_seller_data.items())
		self.connection.execute(
			f'UPDATE seller '
			f'SET {set_params}'
			f'WHERE id = {account_id} '
		)


class CitiesService:
	def __init__(self, connection):
		self.connection = connection

	def get_cities(self, city_name=None):
		query = 'SELECT * ' \
		        'FROM city '
		if city_name:
			query += f'WHERE lower(name) LIKE lower("{city_name}")'
		cur = self.connection.execute(query)
		cities = cur.fetchall()
		return [dict(row) for row in cities]

	def add_city(self, city_name):
		query = f'INSERT OR IGNORE INTO city (name) ' \
		        f'VALUES ("{city_name}")'
		self.connection.execute(query)
		self.connection.commit()

	def create_zip_code(self, zip_code, city_id):
		self.connection.execute(
			f'INSERT OR IGNORE INTO zipcode (zip_code, city_id) '
			f'VALUES ({zip_code}, {city_id})'
		)