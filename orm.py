import datetime, os, hashlib
import Image

from sqlalchemy import and_
from sqlalchemy.orm import mapper, relation, backref

import tables, strorder, cfg

import os


class Instance(object):

    def __init__(self, name):
        self.name = name

    def insert_member(self, pos, member):
        strorder.insert(self, pos, member)

    def append_member(self, member):
        strorder.append(self, member)

    def insert_tag(self, pos, tag):
        strorder.insert(self, pos, tag)

    def append_tag(self, tag):
        strorder.append(self, tag)

    def insert_circular(self, pos, circular):
        strorder.insert(self, pos, circular)

    def append_circular(self, circular):
        strorder.append(self, circular)

    def insert_entrance(self, pos, entrance):
        strorder.insert(self, pos, entrance)

    def append_entrance(self, entrance):
        strorder.append(self, entrance)


class Member(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __unicode__(self):
        s = "\n".join(u"%s=%s" % (key, getattr(self, str(key).split(".", 1)[1])) for key in tables.member_table.columns)
        s += "\ntags=%s" % " ".join(tag.name for tag in self.tags)
        return s


class Change(object):

    def __init__(self, text, note, member, editor):
        self.text = text
        self.note = note
        self.member_id = member.id
        self.editor_id = editor.id


class Tag(object):

    def __init__(self, name, description, visible, photopath, photographer):
        self.name = name
        self.description = description
        self.visible = visible
        self.photopath = photopath
        self.photographer = photographer


class Entrance(object):

    def __init__(self, url, expire):
        self.url = url
        self.expire = expire


class Link(object):

    def __init__(self, uuid, member, entrance):
        self.uuid = uuid
        self.member_id = member.id
        self.entrance_id = entrance.id


class Circular(object):

    def __init__(self, name, title, html, email):
        self.name = name
        self.title = title
        self.html = html
        self.email = email

    def insert_attachment(self, pos, attachment):
        strorder.insert(self, pos, attachment)

    def append_attachment(self, attachment):
        strorder.append(self, attachment)


class Message(object):

    def __init__(self, member, circular, access_by=None):
        self.member_id = member.id
        self.circular_id = circular.id
        if access_by:
            self.access_by = access_by
            self.access_when = datetime.datetime.now()


class Attachment(object):

    def __init__(self, name, mimetype, data):
        self.name = name
        self.mimetype = mimetype
        self.data = data


class Photo(object):

    def __init__(self, name, tag, allow_labels):
        self.name = name
        self.tag = tag
        self.tag_id = tag.id
        self.hash = None
        self.allow_labels = allow_labels
        self.refresh()

    def refresh(self):
        i = Image.open(self.filename)
        md5 = hashlib.md5()
        f = open(self.filename)
        chunk = f.read(2**16)
        while chunk:
            md5.update(chunk)
            chunk = f.read()
        f.close()
        hash = unicode(md5.hexdigest())
        if self.hash != hash:
            self.hash = hash
            self.width, self.height = i.size
            self.size = os.path.getsize(self.filename)
            i.thumbnail((cfg.mid_size, cfg.mid_size), Image.ANTIALIAS)
            i.save(self.midname, "JPEG")
            self.midwidth, self.midheight = i.size
            self.midsize = os.path.getsize(self.midname)
            i.thumbnail((cfg.thumb_size, cfg.thumb_size), Image.ANTIALIAS)
            i.save(self.thumbname, "JPEG")
            self.thumbwidth, self.thumbheight = i.size
            self.thumbsize = os.path.getsize(self.thumbname)

    def _filename(self):
        return os.path.join(self.tag.photopath, self.name)

    def _midname(self):
        return os.path.join(cfg.midpath, "%s.jpg" % self.hash)

    def _thumbname(self):
        return os.path.join(cfg.thumbpath, "%s.jpg" % self.hash)

    filename = property(_filename)
    midname = property(_midname)
    thumbname = property(_thumbname)


class PhotoLabel(object):

    def __init__(self, photo, top, left, width, height, text):
        self.photo_id = photo.id
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.text = text


mapper(Instance, tables.instance_table,
       properties={"members": relation(Member,
                                       backref="instance",
                                       order_by=[tables.member_table.c.instance_order]),
                   "tags": relation(Tag,
                                    backref="instance",
                                    order_by=[tables.tag_table.c.instance_order]),
                   "circulars": relation(Circular,
                                         backref="instance",
                                         order_by=[tables.circular_table.c.instance_order]),
                   "entrances": relation(Entrance,
                                         backref="instance",
                                         order_by=[tables.entrance_table.c.instance_order])})

mapper(Member, tables.member_table,
       properties={"changes": relation(Change,
                                       backref="member",
                                       primaryjoin=tables.member_table.c.id==tables.change_table.c.member_id,
                                       order_by=[tables.change_table.c.timestamp]),
                   "edits": relation(Change,
                                     backref="editor",
                                     primaryjoin=tables.member_table.c.id==tables.change_table.c.editor_id,
                                     order_by=[tables.change_table.c.timestamp]),
                   "links": relation(Link,
                                     backref="member",
                                     primaryjoin=and_(tables.member_table.c.id==tables.link_table.c.member_id,
                                                      tables.entrance_table.c.id==tables.link_table.c.entrance_id),
                                     order_by=[tables.entrance_table.c.instance_order]),
                   "tags": relation(Tag,
                                    secondary=tables.member_tag_table,
                                    backref=backref("members", order_by=tables.member_table.c.instance_order),
                                    order_by=[tables.tag_table.c.instance_order]),
                   "entrances": relation(Entrance,
                                         secondary=tables.link_table,
                                         backref=backref("members", order_by=tables.member_table.c.instance_order),
                                         order_by=[tables.entrance_table.c.instance_order]),
                   "messages": relation(Message,
                                        backref="member",
                                        primaryjoin=and_(tables.member_table.c.id==tables.message_table.c.member_id,
                                                         tables.circular_table.c.id==tables.message_table.c.circular_id),
                                        order_by=[tables.circular_table.c.instance_order])})

mapper(Change, tables.change_table)

mapper(Tag, tables.tag_table,
       properties={"photos": relation(Photo,
                                      backref="tag",
                                      order_by=[tables.photo_table.c.name])})

mapper(Entrance, tables.entrance_table,
       properties={"links": relation(Link,
                                     backref="entrance",
                                     primaryjoin=and_(tables.member_table.c.id==tables.link_table.c.member_id,
                                                      tables.entrance_table.c.id==tables.link_table.c.entrance_id),
                                     order_by=[tables.member_table.c.instance_order])})

mapper(Link, tables.link_table)

mapper(Circular, tables.circular_table,
       properties={"messages": relation(Message,
                                        backref="circular",
                                        primaryjoin=and_(tables.member_table.c.id==tables.message_table.c.member_id,
                                                         tables.circular_table.c.id==tables.message_table.c.circular_id),
                                        order_by=[tables.member_table.c.instance_order]),
                   "attachments": relation(Attachment,
                                          backref="circular",
                                          order_by=[tables.attachment_table.c.circular_order])})

mapper(Message, tables.message_table)

mapper(Attachment, tables.attachment_table)

mapper(Photo, tables.photo_table,
       properties={"labels": relation(PhotoLabel,
                                      backref="photo")})

mapper(PhotoLabel, tables.photo_label_table)


if __name__ == "__main__":
    import xml.sax
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import cfg
    engine = create_engine(cfg.db)
    Session = sessionmaker(bind=engine)
    session = Session()
    instance = Instance(cfg.instance)
    session.add(instance)

    class LoadHandler(xml.sax.handler.ContentHandler):

        def __init__(self):
            self.tags = {}

        def startElement(self, name, attrs):
            if name == "tag":
                tag = Tag(attrs["name"], attrs["description"], attrs["visible"] == "True", None, None)
                self.tags[attrs["name"]] = tag
                instance.append_tag(tag)
            if name == "member":
                data = dict([(str(key), key != "birthday" and value or datetime.date(*map(int, value.split(".")[::-1])))
                             for key, value in attrs.items()
                             if key not in ["tags"]])
                if data.has_key("passwd"):
                    print "creating initial user account for %(firstname)s %(lastname)s, login %(login)s, password %(passwd)s" % data
                    data["salt"] = unicode(os.urandom(16).encode("hex"))
                    data["passwd"] = unicode(hashlib.md5((u"%s%s" % (data["salt"], data["passwd"])).encode("utf-8")).hexdigest())
                self.member = Member(**data)
                instance.append_member(self.member)
                for tag in attrs["tags"].split():
                    self.member.tags.append(self.tags[tag])

        def characters(self, content):
            if content.strip():
                self.member.notes = content

    xml.sax.parse(open(cfg.init), LoadHandler())

    session.commit()
    session.close()
    engine.dispose()
