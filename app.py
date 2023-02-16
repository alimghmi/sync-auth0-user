import logging
import multiprocessing

from decouple import config

from client import auth0
from database import mssql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=None,
)


class App:
    """
    A class for syncing users on a SQL Server table with Auth0 users via the Management API.

    Attributes:
        IGNROE_USERS (list): A list of usernames to ignore during syncing.

    Methods:
        __init__: Initializes the App class.
        run: Syncs the users on the SQL Server table with Auth0 users.
        sync_add_user: Adds new users from the SQL Server table to Auth0.
        sync_delete_user: Deletes users from Auth0 if they are not on the SQL Server table.
        sync_update_user_role: Updates the roles of users on Auth0 based on their roles on the SQL Server table.
        add_auth0_user: Adds a user to Auth0.
        delete_auth0_user: Deletes a user from Auth0.
        get_db_user: Retrieves users from the SQL Server table.
        get_auth0_user: Retrieves users from Auth0.
        fetch_user_role: Retrieves the roles of users on Auth0.
        get_auth0_role: Retrieves the roles available on Auth0.
        generate_user_list: Generates lists of users on the SQL Server table and on Auth0.
        translate_roles: Translates roles from the SQL Server table to roles available on Auth0.
        get_user: Retrieves a user from a collection based on their username or email.
        get_auth0_user_roles: Retrieves the roles of a user on Auth0.
    """

    IGNROE_USERS = config(
        "CLIENT_IGNORE_USERS",
        default="admin",
        cast=lambda v: [
            x.lower().strip() for x in v.split(",") if x.lower().strip() != ""
        ],
    )

    def __init__(self):
        """
        Initializes the App object by setting up database and Auth0 API connections,
        retrieving users from both sources, and generating a list of users to sync.
        """
        self.logger = logging.getLogger()
        self.db = mssql.MSSQLDatabase()
        self.api = auth0.Client()
        self.db_users = self.get_db_user()[:10]
        self.roles = self.get_auth0_role()
        self.users = self.get_auth0_user()
        self.users_roles = self.fetch_user_role()
        self.generate_user_list()

    def run(self):
        """
        Runs the synchronization process, including adding, deleting, and updating users as necessary.
        """
        self.logger.info(f"Found {len(self.db_users)} users in the database.")
        self.logger.info(f"Found {len(self.users)} users in Auth0.")
        self.logger.info(f"Found {len(self.roles)} roles in Auth0.")
        self.logger.info(
            f"Found {len(self.IGNROE_USERS)} users in ignore list"
        )
        self.logger.info("Starting synchronization process...")
        self.sync_update_user_role()
        self.sync_add_user()
        self.sync_delete_user()
        self.logger.info("Synchronization process complete.")

    def sync_add_user(self):
        """
        Adds any users found in the database but not in Auth0.
        """
        self.logger.info("Syncing new users...")
        for user in self.db_user_list:
            if user in self.user_list:
                continue

            user_data = self.get_user(self.db_users, user)

            role_id, _ = self.translate_roles(user_data["role"])
            user_id = self.add_auth0_user(
                user_data["email"], user_data["password"], role_id
            )
            self.logger.info(
                f'Added new user {user_data["email"]}, with role {role_id} and ID {user_id}.'
            )

    def sync_delete_user(self):
        """
        Deletes any users found in Auth0 but not in the database.
        """
        self.logger.info("Syncing deleted users...")
        for user in self.user_list:
            if user in self.IGNROE_USERS:
                continue

            if user not in self.db_user_list:
                user_data = self.get_user(self.users, user)
                self.api.delete_user(user_data["user_id"])
                self.logger.info(
                    f'Deleted user {user_data["email"]} with ID {user_data["user_id"]}.'
                )

    def sync_update_user_role(self):
        """
        Updates the roles of any users found in both the database and Auth0, if necessary.
        """
        self.logger.info("Syncing updated user roles...")
        for user in self.user_list:
            if user in self.IGNROE_USERS:
                continue

            if user not in self.db_user_list:
                continue

            db_user_data = self.get_user(self.db_users, user)
            auth0_user_data = self.get_user(self.users, user)
            role_id, _ = self.translate_roles(db_user_data["role"])
            if len(self.users_roles[user]) == 0:
                self.api.assign_role(auth0_user_data["user_id"], role_id)

            if not any([role == role_id for role in self.users_roles[user]]):
                for _role_id in self.users_roles[user]:
                    self.api.unassign_role(
                        auth0_user_data["user_id"], _role_id
                    )
                    self.logger.info(
                        f'Unassign {_role_id} role to user {auth0_user_data["email"]} with ID {auth0_user_data["user_id"]}.'
                    )

                self.api.assign_role(auth0_user_data["user_id"], role_id)
                self.logger.info(
                    f'Assign {role_id} role to user {auth0_user_data["email"]} with ID {auth0_user_data["user_id"]}.'
                )

    def add_auth0_user(self, email, password, role_id):
        user_id = self.api.add_user(email, password)
        self.api.assign_role(user_id, role_id)
        return user_id

    def delete_auth0_user(self, user_id):
        return self.api.delete_user(user_id)

    def get_db_user(self):
        def parse_data(item):
            item["username"] = item["username"].lower().strip()
            item["email"] = item["email"].lower().strip()
            return item

        result = self.db.select_table("[clients].[users_mock]").to_dict(
            "records"
        )
        return list(map(parse_data, result))

    def get_auth0_user(self):
        users = self.api.get_connection_users()
        return users

    def fetch_user_role(self):
        user_ids = [user["user_id"] for user in self.users]
        user_emails = [user["email"] for user in self.users]
        with multiprocessing.Pool() as pool:
            results = [
                pool.apply_async(
                    self.get_auth0_user_roles,
                    (
                        self.api,
                        user_id,
                    ),
                )
                for user_id in user_ids
            ]
            user_roles = {
                user_id: result.get()
                for user_id, result in zip(user_emails, results)
            }

        return user_roles

    def get_auth0_role(self):
        roles = self.api.get_roles()
        return {role["id"]: role for role in roles}

    def generate_user_list(self):
        self.user_list = [i["email"].lower().strip() for i in self.users]
        self.db_user_list = [
            i["username"].lower().strip() for i in self.db_users
        ]
        return

    def translate_roles(self, db_role):
        db_role = db_role.lower()
        for role in self.roles.values():
            role_name = role["name"].lower().replace("superset_", "")
            if db_role == role_name:
                return role["id"], role

    @staticmethod
    def get_user(collection, username, key=None):
        key = "username" if not key else key
        for item in collection:
            if key not in item:
                key = "email"

            if item[key].lower() == username.lower():
                return item

    @staticmethod
    def get_auth0_user_roles(api, user_id):
        try:
            roles = api.get_user_roles(user_id)
            return [role["id"] for role in roles]
        except Exception:
            return []
