from discord_connections.datatypes import Metadata, MetadataField, MetadataType


# CREATION OF METADATA CLASS
class MySuperMetadata(Metadata):
    platform_name = 'My Cool Name'
    books_read = MetadataField(MetadataType.INT_GTE, 'books read', 'total books read')
    hours_spent = MetadataField(MetadataType.INT_GTE, 'hours reading', 'hours spend reading books')
    # field_three = ...
    # field_four = ...
    # field_five = ...

    # NOTE: An application can have a maximum of 5 metadata records, more:
    # https://discord.com/developers/docs/resources/application-role-connection-metadata


if __name__ == '__main__':
    # CHECKING THE SCHEMA
    print('Schema:', MySuperMetadata.to_schema())

    # INSTANTIATING METADATA
    # ✔️ Metadata can be provided as a dict
    a = MySuperMetadata({'books_read': 1, 'hours_spent': 11, 'platform_username': 'Username'})
    assert a.books_read.value == 1
    assert a.hours_spent.value == 11
    assert a.platform_username == 'Username'
    print(f"{a=}")

    # ✔️ Metadata can be provided as a k/w arguments
    b = MySuperMetadata(books_read=2)
    assert b.books_read.value == 2
    assert b.hours_spent.value is None
    assert b.platform_username is None
    print(f"{b=}")

    # ✔️ Metadata can be set directly, and it will be converted into `MetadataField`
    c = MySuperMetadata()
    c.books_read = 3
    assert type(c.books_read) == MetadataField
    assert c.books_read.value == 3
    print(f"{c=}")

    # ❌ Args and kwargs can`t be provided at the same time
    # d = MySuperMetadata({'books_read': 4}, hours_spent=44)
    # >>> ValueError: Only args OR kwargs can be provided at the same time
