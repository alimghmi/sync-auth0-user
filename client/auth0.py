import time

import requests
from decouple import config


class Client:

    MAX_RETRIES = config("AUTH0_MAX_RETRIES", cast=int, default=3)
    BACKOFF_FACTOR = config("AUTH0_BACKOFF_FACTOR", cast=int, default=2)
    AUTH0_URL = config("AUTH0_URL", cast=str)
    AUTH0_CLIENT_ID = config("AUTH0_CLIENT_ID", cast=str)
    AUTH0_CLIENT_SECRET = config("AUTH0_CLIENT_SECRET", cast=str)
    AUTH0_CONNECTION = config("AUTH0_CONNECTION", cast=str)

    def __init__(self):
        self.token = self.get_token()
        self.headers = self.get_headers()

    def request(self, *args, **kwargs):
        retry = 0
        while retry < self.MAX_RETRIES:
            try:
                response = requests.request(*args, **kwargs)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                retry += 1
                if retry == self.MAX_RETRIES:
                    raise e
                else:
                    sleep_time = self.BACKOFF_FACTOR**retry
                    time.sleep(sleep_time)

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_token(self):
        headers = {"content-type": "application/json"}
        payload = {
            "client_id": self.AUTH0_CLIENT_ID,
            "client_secret": self.AUTH0_CLIENT_SECRET,
            "audience": f"{self.AUTH0_URL}/api/v2/",
            "grant_type": "client_credentials",
        }
        response = self.request(
            "POST",
            f"{self.AUTH0_URL}/oauth/token",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_roles(self):
        url = f"{self.AUTH0_URL}/api/v2/roles"
        response = self.request("GET", url, headers=self.headers)
        response.raise_for_status()
        roles = response.json()
        return roles

    def get_connection_users(self):
        url = f"{self.AUTH0_URL}/api/v2/users"
        params = {
            "connection": self.AUTH0_CONNECTION,
            "search_engine": "v3",
        }
        response = self.request(
            "GET", url, headers=self.headers, params=params
        )
        response.raise_for_status()
        users = response.json()
        return users

    def add_user(self, email, password, user_metadata={}, app_metadata={}):
        url = f"{self.AUTH0_URL}/api/v2/users"
        data = {
            "connection": self.AUTH0_CONNECTION,
            "email": email,
            "password": password,
            "verify_email": False,
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
        }
        response = self.request("POST", url, json=data, headers=self.headers)
        if response.status_code == 201:
            return response.json()["user_id"]
        else:
            raise Exception(
                f"Failed to add user to Auth0. Status code: {response.status_code}, Response: {response.json()}"
            )

    def delete_user(self, user_id):
        url = f"{self.AUTH0_URL}/api/v2/users/{user_id}"
        response = self.request("DELETE", url, headers=self.headers)
        if response.status_code == 204:
            return True
        else:
            raise Exception(
                f"Failed to delete user from Auth0. Status code: {response.status_code}, Response: {response.json()}"
            )

    def get_user_roles(self, user_id):
        url = f"{self.AUTH0_URL}/api/v2/users/{user_id}/roles"
        response = self.request("GET", url, headers=self.headers)
        response.raise_for_status()
        roles = response.json()
        return roles

    def assign_role(self, user_id, role_id):
        url = f"{self.AUTH0_URL}/api/v2/users/{user_id}/roles"
        data = {"roles": [role_id]}
        response = requests.post(url, json=data, headers=self.headers)
        if response.status_code == 204:
            return True
        else:
            raise Exception(
                f"Failed to assign role to user. Status code: {response.status_code}, Response: {response.json()}"
            )

    def unassign_role(self, user_id, role_id):
        url = f"{self.AUTH0_URL}/api/v2/users/{user_id}/roles"
        data = {"roles": [role_id]}
        response = requests.delete(url, json=data, headers=self.headers)
        if response.status_code == 204:
            return True
        else:
            raise Exception(
                f"Failed to unassign role from user. Status code: {response.status_code}, Response: {response.json()}"
            )
