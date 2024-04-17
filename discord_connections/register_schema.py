"""
Import from string is basically copied from uvicorn.
"""
import asyncio
import importlib
import sys
from typing import Any

import click
import environ

from discord_connections import Client as ConnectionsClient


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: Any) -> Any:
    if not isinstance(import_str, str):
        return import_str

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise ImportFromStringError(
            f'Import string must be in format "<path.to.module>:<MetadataModel>" (got: {import_str}).'
        )

    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError as exc:
        if exc.name != module_str:
            raise exc from None
        raise ImportFromStringError(
            f'Could not import module "{module_str}".'
        )

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        raise ImportFromStringError(
            f'Attribute "{attrs_str}" not found in module "{module_str}".'
        )

    return instance


@click.command()
@click.argument('path_to_model')
@click.option('--client_id')
@click.option('--client_secret')
@click.option('--redirect_uri')
@click.option('--discord_token')
@click.option('env_file', '--env', type=click.Path(exists=True))
def register(
    path_to_model: str,
    client_id: int,
    client_secret: str,
    redirect_uri: str,
    discord_token: str,
    env_file: str
) -> None:
    metadata_model = import_from_string(path_to_model)
    try:
        env = environ.Env()
        if env_file:
            env.read_env(env_file)
        connections_client = ConnectionsClient(
            client_id=client_id or env.int('CLIENT_ID'),
            client_secret=client_secret or env('CLIENT_SECRET'),
            redirect_uri=redirect_uri or env('REDIRECT_URI'),
            discord_token=discord_token or env('DISCORD_TOKEN'),
        )
    except Exception as e:
        click.echo(f'Error occurred during client initialization:\n{e}')
        return

    click.echo(f'Trying to register metadata schema...')

    try:
        response = asyncio.run(connections_client.register_metadata_schema(metadata_model))
    except Exception as e:
        click.echo(f'Error occurred during metadata schema registration:\n{e}')
        click.echo(f'Your metadata schema: {metadata_model.to_schema()}')
    else:
        click.echo(f'Metadata schema registered successfully: {response}')


if __name__ == '__main__':
    register()
