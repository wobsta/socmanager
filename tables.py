import datetime

from sqlalchemy import __version__ as sqlalchemy_version
from sqlalchemy import MetaData, Table, Column, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy import Integer, Unicode, String, Boolean, Date, DateTime, Numeric
if sqlalchemy_version.startswith("0.5"):
    from sqlalchemy import Binary as LargeBinary
else:
    from sqlalchemy import LargeBinary

metadata = MetaData()

instance_table = Table("instance", metadata,
                       Column("id", Integer, primary_key=True),
                       Column("name", Unicode, unique=True, nullable=False))

member_table = Table("member", metadata,
                     Column("id", Integer, primary_key=True),
                     Column("login", Unicode, unique=True),
                     Column("salt", Unicode),
                     Column("passwd", Unicode),
                     Column("gender", Unicode, nullable=False),
                     Column("title", Unicode),
                     Column("firstname", Unicode, nullable=False),
                     Column("lastname", Unicode, nullable=False),
                     Column("co", Unicode),
                     Column("street", Unicode),
                     Column("zip", Unicode),
                     Column("city", Unicode),
                     Column("lateral", Numeric(precision=8, scale=6)),
                     Column("longitudinal", Numeric(precision=9, scale=6)),
                     Column("email", Unicode),
                     Column("phone", Unicode),
                     Column("birthday", Date),
                     Column("note", Unicode),
                     Column("instance_order", String, nullable=False),
                     Column("instance_id", Integer, ForeignKey("instance.id"), nullable=False),
                     CheckConstraint("gender in ('female', 'male')"))

change_table = Table("change", metadata,
                     Column("id", Integer, primary_key=True),
                     Column("text", Unicode),
                     Column("note", Unicode),
                     Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                     Column("editor_id", Integer, ForeignKey("member.id"), nullable=False),
                     Column("timestamp", DateTime, default=datetime.datetime.now))

tag_table = Table("tag", metadata,
                  Column("id", Integer, primary_key=True),
                  Column("name", Unicode, unique=True, nullable=False),
                  Column("description", Unicode),
                  Column("visible", Boolean, nullable=False),
                  Column("photopath", Unicode),
                  Column("photographer", Unicode),
                  Column("instance_order", String, nullable=False),
                  Column("instance_id", Integer, ForeignKey("instance.id"), nullable=False),
                  UniqueConstraint("instance_id", "instance_order"))

member_tag_table = Table("member_tag", metadata,
                         Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                         Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                         UniqueConstraint("member_id", "tag_id"))

entrance_table = Table("entrance", metadata,
                       Column("id", Integer, primary_key=True),
                       Column("url", Unicode, nullable=False),
                       Column("expire", Date, nullable=False),
                       Column("instance_order", String, nullable=False),
                       Column("instance_id", Integer, ForeignKey("instance.id"), nullable=False),
                       UniqueConstraint("instance_id", "instance_order"))

link_table = Table("link", metadata,
                   Column("id", Integer, primary_key=True),
                   Column("uuid", Unicode, unique=True, nullable=False),
                   Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                   Column("entrance_id", Integer, ForeignKey("entrance.id"), nullable=False),
                   UniqueConstraint("member_id", "entrance_id"))

circular_table = Table("circular", metadata,
                       Column("id", Integer, primary_key=True),
                       Column("name", Unicode, unique=True, nullable=False),
                       Column("title", Unicode, nullable=False),
                       Column("html", Unicode, nullable=False),
                       Column("email", Unicode, nullable=False),
                       Column("created", DateTime, default=datetime.datetime.now),
                       Column("instance_order", String, nullable=False),
                       Column("instance_id", Integer, ForeignKey("instance.id"), nullable=False),
                       UniqueConstraint("instance_id", "instance_order"))

message_table = Table("message", metadata,
                      Column("id", Integer, primary_key=True),
                      Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                      Column("circular_id", Integer, ForeignKey("circular.id"), nullable=False),
                      Column("access_by", Unicode),
                      Column("access_when", DateTime),
                      CheckConstraint("access_by in ('online', 'snailmail', 'phone')"),
                      UniqueConstraint("member_id", "circular_id"))

attachment_table = Table("attachment", metadata,
                         Column("id", Integer, primary_key=True),
                         Column("name", Unicode, nullable=False),
                         Column("mimetype", Unicode, nullable=False),
                         Column("data", LargeBinary, nullable=False),
                         Column("circular_order", String, nullable=False),
                         Column("circular_id", Integer, ForeignKey("circular.id"), nullable=False),
                         UniqueConstraint("name", "circular_id"),
                         UniqueConstraint("circular_id", "circular_order"))

photo_table = Table("photo", metadata,
                    Column("id", Integer, primary_key=True),
                    Column("name", Unicode, nullable=False),
                    Column("hash", Unicode, nullable=False, unique=True),
                    Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                    Column("width", Integer, nullable=False),
                    Column("height", Integer, nullable=False),
                    Column("size", Integer, nullable=False),
                    Column("thumbwidth", Integer, nullable=False),
                    Column("thumbheight", Integer, nullable=False),
                    Column("thumbsize", Integer, nullable=False),
                    Column("midwidth", Integer, nullable=False),
                    Column("midheight", Integer, nullable=False),
                    Column("midsize", Integer, nullable=False),
                    Column("allow_labels", Boolean, nullable=False),
                    UniqueConstraint("name", "tag_id"))

photo_label_table = Table("photo_label", metadata,
                    Column("id", Integer, primary_key=True),
                    Column("photo_id", Integer, ForeignKey("photo.id"), nullable=False),
                    Column("top", Integer, nullable=False),
                    Column("left", Integer, nullable=False),
                    Column("width", Integer, nullable=False),
                    Column("height", Integer, nullable=False),
                    Column("text", Unicode, nullable=False))


if __name__ == "__main__":
    from sqlalchemy import create_engine
    import cfg
    engine = create_engine(cfg.db)
    metadata.bind = engine
    instance_table.create()
    member_table.create()
    change_table.create()
    tag_table.create()
    member_tag_table.create()
    entrance_table.create()
    link_table.create()
    circular_table.create()
    message_table.create()
    attachment_table.create()
    photo_table.create()
    photo_label_table.create()

