# sync-auth0-user

a Python application for for syncing users on a SQL Server table with Auth0 users via the Auth0 Management API.

## Installation

To install and run the application, follow these steps:

1. Clone the repository to your local machine.
2. Install the required dependencies by running `pip3 install -r requirements.txt`.
3. Set the necessary environment variables, including:
   - `MSSQL_SERVER`: the URL of the SQL Server database.
   - `MSSQL_DATABASE`: the name of database.
   - `MSSQL_USERNAME`: the username of SQL Server.
   - `MSSQL_PASSWORD`: the password of SQL Server.
   - `AUTH0_MAX_RETRIES`: max retry count with auth0 API on failure.
   - `AUTH0_BACKOFF_FACTOR`: the backoff factor of auth0 API client.
   - `AUTH0_URL`: the Auth0 URL.
   - `AUTH0_CLIENT_ID`: the Auth0 client id.
   - `AUTH0_CLIENT_SECRET`: the Auth0 client secret.
   - `AUTH0_CONNECTION`: the Auth0 connection name.
   - `CLIENT_IGNORE_USERS`: the list of users app ignore (comma seperated)

## Usage

To run the application, execute the following command:

```bash
python3 main.py
```

The application will sync the users between the SQL Server database and the Auth0 users via management API.


## Contributing

Contributions are always welcome! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them, with clear commit messages.
4. Push your changes to your fork.
5. Create a pull request.

## License

This app is licensed under the MIT License. See LICENSE for more information.# sync-auth0-user
# sync-auth0-user
