"""
It is oversimplified version of server!

Besides this server, you will need to:
1) implement database to store Discord tokens
2) implement the way you will retrieve data from the resource you are connecting to Discord

Also, check Discord tutorial:
https://discord.com/developers/docs/tutorials/configuring-app-metadata-for-linked-roles
"""


import os

from discord_connections import Client, Metadata
from discord_connections.datatypes import DiscordToken

from flask import Flask, redirect, request, Response, make_response
from flask.sessions import SecureCookieSessionInterface

from examples.a_create_metadata import MySuperMetadata

app = Flask(__name__)
app.secret_key = os.environ.get('COOKIE_SECRET')
session_serializer = SecureCookieSessionInterface().get_signing_serializer(app)

REDIRECT_URL = 'https://discord.com/app'


client = Client(
    client_id=os.environ.get('CLIENT_ID'),
    client_secret=os.environ.get('CLIENT_SECRET'),
    redirect_uri=os.environ.get('REDIRECT_URI'),
    discord_token=os.environ.get('DISCORD_TOKEN')
)


# This route is for authorising into Discord to connect application to your account
# After successful authorisation, application will appear at `User Settings > Authorised Apps`
@app.route('/linked-role')
def linked_role():
    url, state = client.oauth_url

    response = make_response(redirect(url))
    response.set_cookie(key='clientState', value=state, max_age=60 * 5)

    return response


# This route is for callback Discord will send once user authorise the application
# Callback contains token, which must be stored into database
@app.route('/discord-oauth-callback')
async def discord_oauth_callback():
    discord_state = request.args.get('state')
    client_state = request.cookies.get('clientState')
    if client_state != discord_state:
        return Response("State verification failed.", status=403)

    try:
        code = request.args['code']
        token = await client.get_oauth_token(code)

        print("Authorised, token acquired!")

        # Create database to store tokens and save token
        # database.save(token)

        return redirect(REDIRECT_URL)
    except Exception as e:
        return Response(str(e), status=500)


# Route for updating metadata. It can be implemented in different ways, this one receives `userId` via POST request and
# updating metadata for them (check `_update_metadata`)
@app.route('/update-metadata', methods=['POST'])
async def update_metadata():
    try:
        user_id = int(request.form['userId'])
        await _update_metadata(user_id)

        return Response(status=204)
    except Exception as e:
        return Response(str(e), status=500)


async def _update_metadata(user_id: int):
    # Retrieve token from database by `user_id`
    token: DiscordToken = ...  # database.get_token(user_id)

    # Here must be a retrieving data from another resource (e.g. with RestAPI) or from local database by `user_id`
    # data = get_data_for_user(user_id)
    data = ...

    # Then you need to create metadata from retrieved earlier data, which will be pushed to Discord
    metadata: Metadata = MySuperMetadata(**data)

    # Refresh token if needed
    if token.expired:
        token = await client.refresh_token(token)
        # Save new token if needed
        # database.save(token)

    await client.push_metadata(token, metadata.to_dict())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
