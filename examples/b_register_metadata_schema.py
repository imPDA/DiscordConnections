"""
https://discord.com/developers/docs/tutorials/configuring-app-metadata-for-linked-roles#registering-your-metadata-schema
"""


import os

from discord_connections import Client

# Let's use metadata from first example and register it
from a_create_metadata import MySuperMetadata


if __name__ == '__main__':
    # 1) Create a client
    client = Client(
        client_id=os.environ.get('CLIENT_ID'),
        redirect_uri=os.environ.get('REDIRECT_URI'),  # can be None, isn't required for registering the schema
        client_secret=os.environ.get('CLIENT_SECRET'),  # can be None, isn't required for registering the schema
        discord_token=os.environ.get('DISCORD_TOKEN')
    )

    # 2) Register the schema.
    print("Registering the schema:", MySuperMetadata.to_schema())
    client.register_metadata_schema(MySuperMetadata)  # noqa TODO FIX
    print("Done!")


# TODO CLI for registering metadata
