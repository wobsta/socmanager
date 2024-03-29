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
                       Column("name", Unicode, unique=True, nullable=False),
                       Column("onsale_id", Integer, ForeignKey("tag.id")),
                       Column("sale_temporarily_closed", Boolean),
                       Column("bank_transfer_possible", Boolean),
                       Column("shipment_possible", Boolean),
                       Column("description", Unicode))

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
                     Column("lateral", Numeric(precision=8, scale=6), quote=True),
                     Column("longitudinal", Numeric(precision=9, scale=6), quote=True),
                     Column("email", Unicode),
                     Column("email_private", Boolean, nullable=False),
                     Column("phone", Unicode),
                     Column("birthday", Date),
                     Column("birthday_private", Boolean, nullable=False),
                     Column("note", Unicode),
                     Column("subscription_active", Boolean),
                     Column("subscription_holder", Unicode),
                     Column("subscription_iban", Unicode),
                     Column("subscription_bic", Unicode),
                     Column("subscription_pw", Unicode),
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
                  Column("ticket_title", Unicode),
                  Column("ticket_description", Unicode),
                  Column("ticketmap", LargeBinary),
                  Column("ticketmap_width", Integer),
                  Column("ticketmap_height", Integer),
                  Column("ticketmap_latexname", Unicode),
                  Column("recording", Unicode),
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

subscription_table = Table("subscription", metadata,
                           Column("id", Integer, primary_key=True),
                           Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                           Column("amount", Integer, nullable=False),
                           Column("created", DateTime, default=datetime.datetime.now, nullable=False),
                           Column("payed", DateTime))

recording_table = Table("recording", metadata,
                        Column("id", Integer, primary_key=True),
                        Column("member_id", Integer, ForeignKey("member.id"), nullable=False),
                        Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                        Column("account_holder", Unicode, nullable=False),
                        Column("account_iban", Unicode, nullable=False),
                        Column("account_bic", Unicode, nullable=False),
                        Column("amount", Integer, nullable=False),
                        Column("created", DateTime, default=datetime.datetime.now, nullable=False),
                        Column("payed", DateTime),
                        UniqueConstraint("member_id", "tag_id"))

ticket_table = Table("ticket", metadata,
                     Column("id", Integer, primary_key=True),
                     Column("block", Unicode, nullable=False),
                     Column("row", Unicode, nullable=False),
                     Column("seat", Unicode, nullable=False),
                     Column("cathegory", Unicode, nullable=False),
                     Column("wheelchair", Unicode, nullable=False),
                     Column("regular", Integer, nullable=False),
                     Column("image_light", LargeBinary, nullable=False),
                     Column("image_strong", LargeBinary, nullable=False),
                     Column("left", Integer, nullable=False),
                     Column("right", Integer, nullable=False),
                     Column("top", Integer, nullable=False),
                     Column("bottom", Integer, nullable=False),
                     Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                     Column("sold_id", Integer, ForeignKey("sold.id")),
                     CheckConstraint("wheelchair in ('no', 'possible', 'only', 'used')"),
                     UniqueConstraint("block", "row", "seat", "tag_id"))

sold_table = Table("sold", metadata,
                   Column("id", Integer, primary_key=True),
                   Column("name", Unicode, nullable=False),
                   Column("email", Unicode),
                   Column("online", Boolean, nullable=False),
                   Column("bankcode", Unicode),
                   Column("pickupcode", Unicode),
                   Column("payment", Unicode),
                   Column("account_holder", Unicode),
                   Column("account_iban", Unicode),
                   Column("account_bic", Unicode),
                   Column("shipment", Boolean),
                   Column("shipment_firstname", Unicode),
                   Column("shipment_surname", Unicode),
                   Column("shipment_street", Unicode),
                   Column("shipment_zip", Unicode),
                   Column("shipment_city", Unicode),
                   Column("count", Unicode),
                   Column("gender", Unicode, nullable=False),
                   Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                   Column("created", DateTime, default=datetime.datetime.now, nullable=False),
                   Column("payed", DateTime),
                   CheckConstraint("gender in ('female', 'male')"))

coupon_table = Table("coupon", metadata,
                     Column("id", Integer, primary_key=True),
                     Column("amount", Integer, nullable=False),
                     Column("code", Unicode, nullable=False),
                     Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
                     Column("sold_id", Integer, ForeignKey("sold.id")))

newsletter_table = Table("newsletter", metadata,
                         Column("id", Integer, primary_key=True),
                         Column("gender", Unicode, nullable=False),
                         Column("name", Unicode, nullable=False),
                         Column("email", Unicode, nullable=False),
                         Column("instance_id", Integer, ForeignKey("instance.id"), nullable=False),
                         CheckConstraint("gender in ('female', 'male')"))


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
    subscription_table.create()
    subscription_payment_table.create()
    recording_payment_table.create()
    sold_table.create()
    ticket_table.create()
    coupon_table.create()
    newsletter_table.create()
