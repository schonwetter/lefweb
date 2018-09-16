from uuid import uuid4


def get_new_token():
	return str(uuid4())[:8]