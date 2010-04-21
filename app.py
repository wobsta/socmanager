# -*- encoding: utf-8 -*-
#
# socmanager, http://code.google.com/p/socmanager/
# Copyright (C) 2010  André Wobst
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os, sys
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, path)

import site, cfg
if cfg.sitepath:
    site.addsitedir(cfg.sitepath)

import cgi, hashlib, urllib, time, datetime, re, uuid, xml.sax.saxutils, cStringIO, shutil, codecs
cgi.maxlen = 1 * 1024 * 1024 # 1 MB limit for POST data
emailPattern = re.compile(r"[a-zA-Z0-9\!\#\$\%\&\\\"\*\=\?\^\'\(\)\|\~\_\-\.\+\/]+@([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,4}$")

import email.Charset, email.MIMEText, email.MIMEMultipart, email.MIMEBase, email.Utils, smtplib
email.Charset.add_charset("utf-8", email.Charset.SHORTEST, None, None)

try:
    import json
except ImportError:
    import simplejson as json
import web

from sqlalchemy import create_engine, func, Integer, and_, select
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc

import orm, tables

urls = ("/login.html$", "login",
        "/logout.html$", "logout",
        "/link.html$", "link",
        "(/press|/member|/member/photos)$", "add_slash",
        "/member/(index.html|tags.html|privacy.html)?$", "member",
        "/member/data.html$", "member_data",
        "/member/access.html$", "member_access",
        "/member/message/([^/]+)/show.html$", "member_message",
        "/member/message/([^/]+)/(.*)$", "member_message_attachment",
        "/member/photos.html$", "member_photos",
        "/member/photos/([^/]+)/(?:index.html)?$", "member_photos_album",
        "/member/photos/([^/]+)/labels.html$", "member_photos_labels",
        "/member/photos/([^/]+)/(.*)$", "member_photo",
        "/member/admin/nostatus.html$", "member_admin_nostatus",
        "/member/admin/members.html$", "member_admin_members",
        "/member/admin/member/new.html$", "member_admin_member_new",
        "/member/admin/member/changes.html$", "member_admin_member_changes",
        "/member/admin/member/(\d+)/edit.html$", "member_admin_member_edit",
        "/member/admin/member/(\d+)/delete.html$", "member_admin_member_delete",
        "/member/admin/member/(\d+)/changes.html$", "member_admin_member_changes",
        "/member/admin/print.html$", "member_admin_print",
        "/member/admin/tags.html$", "member_admin_tags",
        "/member/admin/tag/new.html$", "member_admin_tag_new",
        "/member/admin/tag/(\d+)/edit.html$", "member_admin_tag_edit",
        "/member/admin/tag/(\d+)/delete.html$", "member_admin_tag_delete",
        "/member/admin/circulars.html$", "member_admin_circulars",
        "/member/admin/circular/copy.html$", "member_admin_circular_copy",
        "/member/admin/circular/new.html$", "member_admin_circular_new",
        "/member/admin/circular/(\d+)/edit.html$", "member_admin_circular_edit",
        "/member/admin/circular/(\d+)/delete.html$", "member_admin_circular_delete",
        "/member/admin/circular/(\d+)/attachments.html$", "member_admin_attachments",
        "/member/admin/circular/(\d+)/attachment/new.html$", "member_admin_attachment_new",
        "/member/admin/circular/(\d+)/attachment/(\d+)/show.html$", "member_admin_attachment_show",
        "/member/admin/circular/(\d+)/attachment/(\d+)/edit.html$", "member_admin_attachment_edit",
        "/member/admin/circular/(\d+)/attachment/(\d+)/delete.html$", "member_admin_attachment_delete",
        "/member/admin/links.html$", "member_admin_links",
        "/member/admin/link/new.html$", "member_admin_link_new",
        "/member/admin/link/(\d+)/edit.html$", "member_admin_link_edit",
        "/member/admin/link/(\d+)/delete.html$", "member_admin_link_delete",
        "/member/admin/link/(\d+)/email.html$", "member_admin_link_email",
        "/(?!member/)(.*)$", "pages")


engine = create_engine(cfg.db)

def load_sqla(handler):
    web.ctx.orm = scoped_session(sessionmaker(bind=engine))
    try:
        result = handler()
    except web.HTTPError:
        web.ctx.orm.commit()
        raise
    except:
        web.ctx.orm.rollback()
        raise
    else:
        web.ctx.orm.commit()
    return result


app = web.application(urls, locals())
app.add_processor(load_sqla)

render = web.template.render(os.path.join(path, "templates"), globals={"str": str, "sorted": sorted})

# {{{ helper
def TeX_escape(value):
    for replace, by in [("\\", "\\textbackslash"), 
                        ("$", "\\$"), ("&", "\\&"), ("#", "\\#"), ("_", "\\_"), ("%", "\\%"),
                        ("^", "\\textasciicircum"), ("~", "\\texttilde"), ("<", "\\textlower"), (">", "\\textgreater"),
                        ("{", "\\{"), ("}", "\\}"), ("|", "\\textbar"),
                        ("\r\n", "\n"), ("\r", "\n"), ("\n", "\\string n") # newlines -> "\string n"
                        ]:
        value = value.replace(replace, by)
    return value
# }}} helper

# {{{ public
LoginForm = web.form.Form(web.form.Textbox("login", description="Benutzername"),
                          web.form.Password("passwd", description="Passwort"),
                          web.form.Hidden("next"),
                          web.form.Button("Login", type="submit"))

class login(object):

    def GET(self):
        form = LoginForm()
        form.validates()
        return render.page("/login.html", render.login(form), None)

    def POST(self):
        form = LoginForm()
        form.validates()
        if form.d.login:
            try:
                member = web.ctx.orm.query(orm.Member).filter_by(login=form.d.login).one()
            except NoResultFound:
                time.sleep(1)
                return render.page("/login.html", render.login(form, failed=True), None)
            if hashlib.md5((u"%s%s" % (member.salt, form.d.passwd)).encode("utf-8")).hexdigest() != member.passwd:
                time.sleep(1)
                return render.page("/login.html", render.login(form, failed=True), None)
            salt = os.urandom(16).encode("hex")
            hash = hashlib.md5(("".join([cfg.secret, salt, str(member.id)])).encode("utf-8")).hexdigest()
            web.setcookie(cfg.cookie, " ".join([hash, salt, str(member.id)]), 86400)
            if form.d.next and form.d.next.find(":") == -1 and form.d.next.lower().find("%3a") == -1:
                raise web.seeother(form.d.next)
            raise web.seeother("/member/index.html")
        return render.page("/login.html", render.login(form), None)


class logout(object):

    def POST(self):
        web.setcookie(cfg.cookie, "", -1)
        return render.page("/logout.html", render.logout(), None)


class link(object):

    def GET(self):
        try:
            link = web.ctx.orm.query(orm.Link).filter_by(uuid=web.input().get("uuid", "")).one()
        except NoResultFound:
            return render.page("/login.html", render.login(LoginForm(), failed=True), None)
        if datetime.date.today() > link.entrance.expire:
            return render.page("/login.html", render.login(LoginForm(), failed=True), None)
        salt = os.urandom(16).encode("hex")
        hash = hashlib.md5(("".join([cfg.secret, salt, str(link.member.id)])).encode("utf-8")).hexdigest()
        web.setcookie(cfg.cookie, " ".join([hash, salt, str(link.member.id)]), 86400)
        raise web.seeother(link.entrance.url)


class add_slash(object):

    def GET(self, path):
        raise web.seeother("%s/" % path)


def get_member():
    cookie = web.cookies().get(cfg.cookie, None)
    if cookie:
        try:
            hash, salt, id = urllib.unquote(cookie).decode("utf-8").split(None, 5)
        except ValueError:
            return
        try:
            id = int(id)
        except ValueError:
            return
        if hashlib.md5("".join([cfg.secret, salt, str(id)]).encode("utf-8")).hexdigest() == hash:
            return web.ctx.orm.query(orm.Member).filter_by(id=id).one()


def with_member_info(f):
    def wrapper(self, *args, **kwargs):
        self.member = get_member()
        return f(self, *args, **kwargs)
    return wrapper


def with_member_auth(admin_only=False, active_only=False):
    def with_member_info(f):
        def wrapper(self, *args, **kwargs):
            self.member = get_member()
            if (not self.member or
                (admin_only and "admin" not in [tag.name for tag in self.member.tags]) or
                (active_only and "inaktiv" in [tag.name for tag in self.member.tags])):
                raise web.seeother("/login.html?%s" % (urllib.urlencode({"next": web.ctx.path})))
            return f(self, *args, **kwargs)
        return wrapper
    return with_member_info


class pages(object):

    @with_member_info
    def GET(self, path):
        org_path = None
        if path == "page.html":
            raise web.NotFound()
        if not path:
            path = "index.html"
        elif path == "press/":
            path = "press/index.html"
        elif path == "press.html":
            path = "press/index.html"
            org_path = "/press.html"
        if not path.endswith(".html"):
            raise web.NotFound()
        try:
            content = getattr(render, path[:-5])
        except AttributeError:
            raise web.NotFound()
        return render.page(org_path or "/%s" % path, content(), self.member)
# }}} public

# {{{ member
class member(object):

    @with_member_auth()
    def GET(self, path):
        if not path:
            path = "index.html"
        return render.page("/member/%s" % path, getattr(render.member, path[:-5])(self.member), self.member)


def checkemail(i):
    if not i.email:
        return True
    for email in i.email.split(","):
        if not emailPattern.match(email):
            return False
    return True


def get_birthday(i):
    if not i.birthday:
        return True
    day, month, year = map(int, i.birthday.split("."))
    if year < 1900:
        return False
    return datetime.date(year, month, day)


DataForm = web.form.Form(web.form.Textbox("title", description="akademischer Titel"),
                         web.form.Textbox("firstname", description="Vorname", size=50, readonly="readonly"),
                         web.form.Textbox("lastname", description="Nachname", size=50, readonly="readonly"),
                         web.form.Textbox("co", description="c/o", size=50),
                         web.form.Textbox("street", description="Strasse", size=50),
                         web.form.Textbox("zip", description="PLZ"),
                         web.form.Textbox("city", description="Ort", size=50),
                         web.form.Textbox("lateral", description="Position lateral (siehe Karte unten)", readonly="readonly"),
                         web.form.Textbox("longitudinal", description="Position longitudinal (siehe Karte unten)", readonly="readonly"),
                         web.form.Textbox("phone", description="Telefon (mehrere möglich; auch gern Fax-Nr.)", size=50),
                         web.form.Textbox("email", description="E-Mail (mehrere mit Komma getrennt möglich)", size=50),
                         web.form.Textbox("birthday", description="Geburtstag (freiwillig; Format TT.MM.JJJJ)"),
                         web.form.Textarea("notes", description="Notizen (nur intern verwendet)", cols=50, rows=5),
                         web.form.Button("Daten ändern", type="submit"),
                         validators = [web.form.Validator("Formatfehler in E-Mail-Adresse(n).", checkemail),
                                       web.form.Validator("Ungültiges Geburtsdatum.", get_birthday)])


class member_data(object):

    @with_member_auth()
    def GET(self):
        form = DataForm()
        form.title.value = self.member.title
        form.firstname.value = self.member.firstname
        form.lastname.value = self.member.lastname
        form.co.value = self.member.co
        form.street.value = self.member.street
        form.zip.value = self.member.zip
        form.city.value = self.member.city
        form.lateral.value = self.member.lateral
        form.longitudinal.value = self.member.longitudinal
        form.phone.value = self.member.phone
        form.email.value = self.member.email
        form.birthday.value = self.member.birthday and self.member.birthday.strftime("%d.%m.%Y") or ""
        form.notes.value = self.member.note
        return render.page("/member/data.html", render.member.data(form, cfg.maps_key[web.ctx.protocol]), self.member)

    @with_member_auth()
    def POST(self):
        form = DataForm()
        if form.validates():
            old = unicode(self.member)
            self.member.title = form.d.title
            self.member.co = form.d.co
            self.member.street = form.d.street
            self.member.zip = form.d.zip
            self.member.city = form.d.city
            self.member.lateral = form.d.lateral or None
            self.member.longitudinal = form.d.longitudinal or None
            self.member.phone = form.d.phone
            self.member.email = form.d.email
            birthday = get_birthday(form.d)
            if birthday is True:
                self.member.birthday = None
            else:
                self.member.birthday = birthday
            self.member.note = form.d.notes
            new = unicode(self.member)
            if old != new:
                web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Mitgliederdaten", self.member, self.member))
            raise web.seeother("index.html")
        else:
            return render.page("/member/data.html", render.member.data(form, cfg.maps_key[web.ctx.protocol]), self.member)


def checkoldpasswd(i):
    member = get_member()
    return (not member.passwd and not i.oldpasswd) or hashlib.md5((u"%s%s" % (member.salt, i.oldpasswd)).encode("utf-8")).hexdigest() == member.passwd


def checkloginavailable(i):
    try:
        login_member = web.ctx.orm.query(orm.Member).filter_by(login=i.login).one()
    except NoResultFound:
        return True
    return login_member == get_member()


AccessForm = web.form.Form(web.form.Textbox("login", description="Benutzername (z.B. E-Mail-Adresse)"),
                           web.form.Password("oldpasswd", description="altes Passwort (falls vorhanden)"),
                           web.form.Password("newpasswd", description="neues Passwort"),
                           web.form.Password("newpasswd2", description="neues Passwort wiederholen"),
                           web.form.Button("Zugang einrichten bzw. ändern", type="submit"),
                           validators = [web.form.Validator("Altes Passwort stimmt nicht.", checkoldpasswd),
                                         web.form.Validator("Benutzername wird bereits von einem anderen Chormitglied verwendet.", checkloginavailable),
                                         web.form.Validator("Passwörter sind nicht identisch.", lambda i: i.newpasswd == i.newpasswd2),
                                         web.form.Validator("Passwort darf nicht leer gelassen werden.", lambda i: i.newpasswd != "")])


class member_access(object):

    @with_member_auth()
    def GET(self):
        form = AccessForm()
        form.login.value = self.member.login
        return render.page("/member/access.html", render.member.access(form), self.member)

    @with_member_auth()
    def POST(self):
        form = AccessForm()
        if form.validates():
            old = unicode(self.member)
            self.member.login = form.d.login
            self.member.salt = unicode(os.urandom(16).encode("hex"))
            self.member.passwd = unicode(hashlib.md5((u"%s%s" % (self.member.salt, form.d.newpasswd)).encode("utf-8")).hexdigest())
            new = unicode(self.member)
            if old != new:
                web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Zugangsdaten", self.member, self.member))
            raise web.seeother("index.html")
        else:
            return render.page("/member/access.html", render.member.access(form), self.member)


class member_message(object):

    @with_member_auth()
    def GET(self, id):
        printview = web.ctx.method=="POST"
        if not id.isdigit():
            id = web.ctx.orm.query(orm.Circular).filter_by(name=id).one().id
        message = web.ctx.orm.query(orm.Message).filter_by(member_id=self.member.id).filter_by(circular_id=int(id)).one()
        if not message.access_by:
            message.access_by = u"online"
            message.access_when = datetime.datetime.now()
        icons = dict((attachment.mime, attachment.icon) for attachment in cfg.attachments)
        return render.page("/member/message/X/show.html", render.member.message(message, self.member, icons, printview), self.member, printview=printview)

    POST=GET


class member_message_attachment(object):

    @with_member_auth()
    def GET(self, id, name):
        if not id.isdigit():
            id = web.ctx.orm.query(orm.Circular).filter_by(name=id).one().id
        message = web.ctx.orm.query(orm.Message).filter_by(member_id=self.member.id).filter_by(circular_id=int(id)).one()
        if not message.access_by:
            message.access_by = u"online"
            message.access_when = datetime.datetime.now()
        try:
            attachment, = [attachment for attachment in message.circular.attachments if attachment.name == name]
        except ValueError:
            raise web.NotFound()
        web.header("Content-Type", attachment.mimetype)
        web.header("Content-Disposition", "attachment; filename=%s" % attachment.name)
        return attachment.data


class member_photos(object):

    @with_member_auth(active_only=True)
    def GET(self):
        count = web.ctx.orm.query(orm.Photo.tag_id, func.count().label("count")).group_by(orm.Photo.tag_id).subquery()
        labeled = web.ctx.orm.query(orm.Photo.tag_id, func.count().label("count"),
                                    func.array_to_string(func.array_agg(orm.Photo.name), ",").label("names"))\
                             .filter_by(allow_labels=True).group_by(orm.Photo.tag_id).subquery()
        tags = web.ctx.orm.query(orm.Tag, count.c.count, labeled.c.count, labeled.c.names)\
                          .join((count, orm.Tag.id == count.c.tag_id))\
                          .outerjoin((labeled, orm.Tag.id == labeled.c.tag_id))\
                          .order_by([desc(orm.Tag.instance_order)]).all()
        return render.page("/member/photos.html", render.member.photos(tags), self.member)


class member_photos_album(object):

    @with_member_auth(active_only=True)
    def GET(self, tag):
        photo = web.input().get("photo")
        if photo:
            photo = web.ctx.orm.query(orm.Photo).filter_by(name=photo).join(orm.Tag).filter_by(name=tag).join(orm.Instance).filter_by(name=cfg.instance).one()
            return render.page("/member/photos/X/index.html", render.member.photo(photo), self.member)
        else:
            tag = web.ctx.orm.query(orm.Tag).filter_by(name=tag).join(orm.Instance).filter_by(name=cfg.instance).one()
            page = int(web.input().get("page", "1"))
            return render.page("/member/photos/X/index.html", render.member.album(tag, page), self.member)


class member_photos_labels(object):

    @with_member_auth(active_only=True)
    def GET(self, tag):
        i = web.input()
        photo = web.ctx.orm.query(orm.Photo).filter_by(name=i.photo).join(orm.Tag).filter_by(name=tag).join(orm.Instance).filter_by(name=cfg.instance).one()
        if i.action == "save":
            if i.id == "new":
                label = orm.PhotoLabel(photo, i.top, i.left, i.width, i.height, i.text)
                web.ctx.orm.add(label)
                web.ctx.orm.commit()
            else:
                label = web.ctx.orm.query(orm.PhotoLabel).filter_by(id=int(i.id.split("-")[1])).filter_by(photo=photo).one()
                label.top = i.top
                label.left = i.left
                label.width = i.width
                label.height = i.height
                label.text = i.text
            web.header("Content-Type", "text/json")
            return json.dumps({"annotation_id": "label-%d" % label.id})
        elif i.action == "delete":
            label = web.ctx.orm.query(orm.PhotoLabel).filter_by(id=int(i.id.split("-")[1])).filter_by(photo=photo).one()
            web.ctx.orm.delete(label)
            web.header("Content-Type", "text/json")
            return json.dumps({})
        else:
            web.header("Content-Type", "application/json")
            return json.dumps([{"top": label.top, "left": label.left, "width": label.width, "height": label.height, "text": label.text, "id": "label-%d" % label.id, "editable": True}
                               for label in photo.labels])


class member_photo(object):

    @with_member_auth()
    def GET(self, tag, name):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        photo = session.query(orm.Photo).filter_by(name=name).join(orm.Tag).filter_by(name=tag).join(orm.Instance).filter_by(name=cfg.instance).one()
        try:
            type = web.input().get("type")
            if type == "thumb":
                f = open(photo.thumbname)
            elif type == "mid":
                f = open(photo.midname)
            else:
                f = open(photo.filename)
        except:
            session.close()
            raise web.NotFound()
        web.header("Content-Type", "image/jpeg")
        web.header("Transfer-Encoding", "chunked")
        data = f.read(2**16)
        while data:
            yield data
            data = f.read(2**16)
        f.close()
        session.close()

# }}}

# {{{ admin
class member_admin_work_on_selection(object):

    def members(self):
        ids = web.input().get("selection", "")
        if ids:
            ids = [int(id) for id in ids.split(",")]
        else:
            ids = []
        return web.ctx.orm.query(orm.Member)\
                          .filter(orm.Member.id == func.any(ids))\
                          .join(orm.Instance).filter_by(name=cfg.instance)\
                          .order_by(orm.Member.instance_order)\
                          .all()

class member_admin_nostatus(member_admin_work_on_selection):

    @with_member_auth(admin_only=True)
    def GET(self):
        web.header('Content-Type','text/plain')
        web.header("Transfer-Encoding", "chunked")
        yield ""


# {{{ admin members
class member_admin_members(member_admin_work_on_selection):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("withorwithout", [("with", "mit"), ("without", "ohne")]),
                             web.form.Dropdown("tag", [tag.name for tag in self.instance.tags]),
                             *[web.form.Checkbox(name="member_%i" % member.id) for member in self.instance.members])

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        for member in self.members():
            form["member_%i" % member.id].checked = True
        return render.page("/member/admin/members.html", render.member.admin.members(self.instance, form), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            # The next three lines are strange. They should not be needed. Something in web.py checkboxes is badly broken in recent releases (after 0.32).
            i = web.input()
            for member in self.instance.members:
                form["member_%i" % member.id].checked = i.has_key("member_%i" % member.id)
            def withorwithout(cond):
                if form.d.withorwithout == "with":
                    return cond
                return not cond
            if web.input().get("add"):
                for member in self.instance.members:
                    if withorwithout(form.d.tag in [tag.name for tag in member.tags]):
                        form["member_%i" % member.id].checked = True
            elif web.input().get("remove"):
                for member in self.instance.members:
                    if withorwithout(form.d.tag in [tag.name for tag in member.tags]):
                        form["member_%i" % member.id].checked = False
            elif web.input().get("none"):
                for member in self.instance.members:
                    form["member_%i" % member.id].checked = False
            elif web.input().get("all"):
                for member in self.instance.members:
                    form["member_%i" % member.id].checked = True
            elif web.input().get("invert"):
                for member in self.instance.members:
                    form["member_%i" % member.id].checked = not i.has_key("member_%i" % member.id)
            else:
                members = ",".join(str(member.id) for member in self.instance.members if i.has_key("member_%i" % member.id))
                if web.input().get("print"):
                    raise web.seeother("print.html?selection=%s" % members)
                elif web.input().get("tags"):
                    raise web.seeother("tags.html?selection=%s" % members)
                elif web.input().get("circulars"):
                    raise web.seeother("circulars.html?selection=%s" % members)
                elif web.input().get("links"):
                    raise web.seeother("links.html?selection=%s" % members)
        return render.page("/member/admin/members.html", render.member.admin.members(self.instance, form), self.member)


def get_tags(i, get_list=False):
    if not get_list and not i.tags.split(): # hackish: test for empty/whitespace string
        return True
    return [web.ctx.orm.query(orm.Tag).filter_by(name=tag).join(orm.Instance).filter_by(name=cfg.instance).one()
            for tag in i.tags.split()]


def get_circulars(i, get_list=False):
    if not get_list:
        if not i.messages.split(): # hackish: test for empty/whitespace string
            return True
        else:
            for message in i.messages.split():
                if message.find(":") != -1 and message.split(":", 1)[1] not in ["snailmail", "online"]:
                    return False
    return [(web.ctx.orm.query(orm.Circular).filter_by(name=message.split(":")[0]).join(orm.Instance).filter_by(name=cfg.instance).one(),
             message.find(":") != -1 and message.split(":", 1)[1] or None)
            for message in i.messages.split()]


class member_admin_member_form(object):

    def form(self, skip_member=None):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        members = [member for member in self.instance.members if skip_member is None or member != skip_member]
        return web.form.Form(web.form.Textbox("firstname", description="Vorname", size=50),
                             web.form.Textbox("lastname", description="Nachname", size=50),
                             web.form.Dropdown("pos", [("0", "an erster Position")] +
                                                      [(str(i+1), "nach %s, %s" % (member.lastname, member.firstname))
                                                       for i, member in enumerate(members)], description="Position in der Liste"),
                             web.form.Textbox("title", description="akademischer Titel"),
                             web.form.Dropdown("gender", [("female", "Frau"), ("male", "Herr")], description="Anrede"),
                             web.form.Textbox("co", description="c/o", size=50),
                             web.form.Textbox("street", description="Strasse", size=50),
                             web.form.Textbox("zip", description="PLZ"),
                             web.form.Textbox("city", description="Ort", size=50),
                             web.form.Textbox("lateral", description="Position lateral (siehe Karte unten)", readonly="readonly"),
                             web.form.Textbox("longitudinal", description="Position longitudinal (siehe Karte unten)", readonly="readonly"),
                             web.form.Textbox("phone", description="Telefon (mehrere möglich; auch gern Fax-Nr.)", size=50),
                             web.form.Textbox("email", description="E-Mail (mehrere mit Komma getrennt möglich)", size=50),
                             web.form.Textbox("birthday", description="Geburtstag (Format TT.MM.JJJJ)"),
                             web.form.Textarea("notes", description="Notizen (nur intern verwendet)", cols=50, rows=5),
                             web.form.Textbox("tags", description="Tags", size=50),
                             web.form.Textbox("messages", description="Chorbriefe", size=50),
                             web.form.Button("Speichern", type="submit"),
                             validators = [web.form.Validator("Formatfehler in E-Mail-Adresse(n).", checkemail),
                                           web.form.Validator("Ungültiges Geburtsdatum.", get_birthday),
                                           web.form.Validator("Ungültige Tags.", get_tags),
                                           web.form.Validator("Ungültige Chorbriefe.", get_circulars)])


class member_admin_member_new(member_admin_member_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        if self.instance.circulars:
            form.messages.value = self.instance.circulars[0].name
        return render.page("/member/admin/member/new.html", render.member.admin.member.new(form, cfg.maps_key[web.ctx.protocol]), self.member)

    @with_member_auth()
    def POST(self):
        form = self.form()
        if form.validates():
            data = dict(form.d)
            data["lateral"] = form.d.lateral or None
            data["longitudinal"] = form.d.longitudinal or None
            data["note"] = form.d.notes
            del data["pos"]
            del data["notes"]
            birthday = get_birthday(form.d)
            if birthday is True:
                data["birthday"] = None
            else:
                data["birthday"] = birthday
            del data["tags"]
            del data["messages"]
            member = orm.Member(**data)
            self.instance.insert_member(int(form.d.pos), member)
            member.tags = get_tags(form.d, get_list=True)
            for circular, access_by in get_circulars(form.d, get_list=True):
                web.ctx.orm.add(orm.Message(member, circular, access_by))
            web.ctx.orm.commit()
            web.ctx.orm.add(orm.Change(unicode(member), u"Mitglied neu angelegt", member, self.member))
            raise web.seeother("../members.html")
        else:
            return render.page("/member/admin/member/new.html", render.member.admin.member.new(form, cfg.maps_key[web.ctx.protocol]), self.member)


class member_admin_member_edit(member_admin_member_form):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_member=member)
        form.pos.value = str(self.instance.members.index(member))
        form.title.value = member.title
        form.gender.value = member.gender
        form.firstname.value = member.firstname
        form.lastname.value = member.lastname
        form.co.value = member.co
        form.street.value = member.street
        form.zip.value = member.zip
        form.city.value = member.city
        form.lateral.value = member.lateral
        form.longitudinal.value = member.longitudinal
        form.phone.value = member.phone
        form.email.value = member.email
        form.birthday.value = member.birthday and member.birthday.strftime("%d.%m.%Y") or ""
        form.notes.value = member.note
        form.tags.value = " ".join(tag.name for tag in member.tags)
        form.messages.value = " ".join(message.access_by and "%s:%s" % (message.circular.name, message.access_by) or message.circular.name
                                       for message in member.messages)
        return render.page("/member/admin/member/X/edit.html", render.member.admin.member.edit(form, cfg.maps_key[web.ctx.protocol]), self.member)

    @with_member_auth()
    def POST(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_member=member)
        if form.validates():
            old = unicode(member)
            member.title = form.d.title
            member.gender = form.d.gender
            member.firstname = form.d.firstname
            member.lastname = form.d.lastname
            member.co = form.d.co
            member.street = form.d.street
            member.zip = form.d.zip
            member.city = form.d.city
            member.lateral = form.d.lateral or None
            member.longitudinal = form.d.longitudinal or None
            member.phone = form.d.phone
            member.email = form.d.email
            birthday = get_birthday(form.d)
            if birthday is True:
                member.birthday = None
            else:
                member.birthday = birthday
            member.note = form.d.notes
            member.tags = get_tags(form.d, get_list=True)
            if self.instance.members.index(member) != int(form.d.pos):
                self.instance.members.remove(member)
                self.instance.insert_member(int(form.d.pos), member)
            messages = dict((message.circular_id, message) for message in member.messages)
            for circular, access_by in get_circulars(form.d, get_list=True):
                message = messages.pop(circular.id, None)
                if message:
                    if message.access_by != access_by:
                        message.access_by = access_by
                        if access_by:
                            message.access_when = datetime.datetime.now()
                        else:
                            message.access_when = None
                else:
                    web.ctx.orm.add(orm.Message(member, circular, access_by))
            for message in messages.values():
                web.ctx.orm.delete(message)
            new = unicode(member)
            if old != new:
                web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Mitgliederdaten", member, self.member))
            raise web.seeother("../../members.html")
        else:
            return render.page("/member/admin/member/X/edit.html", render.member.admin.member.edit(form, cfg.maps_key[web.ctx.protocol]), self.member)


class member_admin_member_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/member/X/delete.html", render.member.admin.member.delete(member), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        for change in member.changes:
            web.ctx.orm.delete(change)
        for edit in member.edits:
            web.ctx.orm.delete(edit)
        for link in member.links:
            web.ctx.orm.delete(link)
        for tag in member.tags:
            web.ctx.orm.delete(tag)
        for message in member.messages:
            web.ctx.orm.delete(message)
        web.ctx.orm.delete(member)
        raise web.seeother("../../members.html")


class member_admin_member_changes(object):

    @with_member_auth(admin_only=True)
    def GET(self, id=None):
        query = web.ctx.orm.query(orm.Change).join(orm.Member.changes).join(orm.Instance).filter_by(name=cfg.instance)
        if id:
            member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
            query = query.reset_joinpoint().filter_by(member_id=int(id))
        else:
            member = None
        changes = query.order_by([desc(orm.Change.timestamp)])
        return render.page("/member/admin/member/X/changes.html", render.member.admin.member.changes(changes, member), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id=None):
        query = web.ctx.orm.query(orm.Change).join(orm.Member.changes).join(orm.Instance).filter_by(name=cfg.instance)
        if id:
            query = query.reset_joinpoint().filter_by(member_id=int(id))
        change = query.filter_by(id=web.input().id).one()
        web.ctx.orm.delete(change)
        raise web.seeother("changes.html")
# }}} admin members

# {{{ admin print
PrintForm = web.form.Form(web.form.Dropdown("format", [(format.name, format.description)
                                                       for format in cfg.formats], description="Format"),
                          web.form.Textbox("description", description="ggf. Beschreibung"),
                          web.form.Hidden("selection"),
                          web.form.Button("Erzeugen", type="submit"))

class member_admin_print(member_admin_work_on_selection):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = PrintForm()
        members = self.members()
        form.selection.value = ",".join([str(member.id) for member in members])
        return render.page("/member/admin/print.html", render.member.admin._print(form, members), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        form = PrintForm()
        if form.validates():
            members = self.members()
            format, = [format for format in cfg.formats if format.name == form.d.format]
            if format.merge == "address":
                equal_key = lambda member: (member.co or u"", member.street or member.id, member.zip or u"", member.city or u"")
            else:
                equal_key = lambda member: member.id
            equal_members = {}
            members_groups = []
            for member in members:
                equal = equal_key(member)
                if equal_members.has_key(equal):
                    equal_members[equal].append(member)
                else:
                    merged_members = [member]
                    equal_members[equal] = merged_members
                    members_groups.append(merged_members)
            for merged_members in members_groups:
                merged_members.sort(key=lambda member: member.gender)
            try:
                os.makedirs(cfg.tmppath)
            except OSError:
                pass
            if format.type == "xml":
                filename = os.path.join(cfg.tmppath, "%s.xml" % cfg.instance)
                f = open(filename, "w")
                x = xml.sax.saxutils.XMLGenerator(f, "utf-8")
                x.startDocument()
                x.startElement("members", {})
                x.characters("\n")
                for merged_members in members_groups:
                    x.startElement("memberGroup", {})
                    x.characters("\n")
                    for member in merged_members:
                        x.startElement("member", {})
                        x.characters("\n")
                        for name in ["id", "login", "gender", "title", "firstname", "lastname", "co", "street", "zip", "city",
                                     "lateral", "longitudinal", "email", "phone", "birthday", "note"]:
                            value = member.__dict__[name]
                            if name == "birthday":
                                value = value and value.strftime("%d.%m.%Y") or ""
                            else:
                                value = value and unicode(value) or ""
                            x.startElement(name, {})
                            x.characters("\n%s\n" % value)
                            x.endElement(name)
                            x.characters("\n")
                        x.endElement("member")
                        x.characters("\n")
                    x.endElement("memberGroup")
                    x.characters("\n")
                x.endElement("members")
                x.characters("\n")
                f.close()
                os.system("%s %s %s > %s.xmlresult 2> %s.err" % (cfg.xsltproc, os.path.join(path, "formats", format.xslt), filename, filename[:-4], filename[:-4]))
                web.header("Content-Type", "application/vnd.google-earth.kml+xml")
                web.header("Content-Disposition", "attachment; filename=\"%s.kml\"" % cfg.instance)
                f = open(os.path.join(cfg.tmppath, "%s.xmlresult" % cfg.instance), "rb")
                pdf = f.read()
                f.close()
                return pdf
            else:
                filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
                f = codecs.open(filename, "w", encoding="utf-8")
                f.write(u"\\documentclass{%s}\n" % format.cls.split(".")[0])
                f.write(u"\\usepackage[utf8]{inputenc}\n")
                f.write(u"\\usepackage[T1]{fontenc}\n")
                f.write(u"\\datetime{%s}\n" % datetime.datetime.now().strftime("%d.%m.%Y, %H:%M"))
                f.write(u"\\info{%s}\n" % TeX_escape(form.d.description))
                f.write(u"\\begin{document}\n")
                f.write(u"\\begin{members}%\n")
                for merged_members in members_groups:
                    f.write(u"\\begin{memberGroup}%\n")
                    for member in merged_members:
                        f.write(u"\\begin{member}%\n")
                        for name in ["id", "login", "gender", "title", "firstname", "lastname", "co", "street", "zip", "city",
                                     "lateral", "longitudinal", "email", "phone", "birthday", "note"]:
                            value = member.__dict__[name]
                            if name == "birthday":
                                value = value and value.strftime("%d.%m.%Y") or ""
                            else:
                                value = value and unicode(value) or ""
                            f.write(u"\\member%s{%s}%%\n" % (name.capitalize(), TeX_escape(value)))
                        f.write(u"\\memberTags{%s}%%\n" % ", ".join(tag.name for tag in member.tags))
                        f.write(u"\\end{member}%\n")
                    f.write(u"\\end{memberGroup}%\n")
                f.write(u"\\end{members}%\n")
                f.write(u"\\end{document}\n")
                f.close()
                shutil.copy(os.path.join(path, "formats", format.cls), cfg.tmppath)
                try:
                    os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
                except OSError:
                    pass
                os.system("cd %s; %s %s > %s.out 2>&1" % (cfg.tmppath, cfg.pdflatex, filename, filename[:-4]))
                f = open(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance), "rb")
                pdf = f.read()
                f.close()
                web.header("Content-Type", "application/pdf")
                web.header("Content-Disposition", "attachment; filename=\"%s.pdf\"" % cfg.instance)
                return pdf
        else:
            return render.page("/member/admin/print.html", render.member.admin._print(form, members), self.member)
# }}} admin print

# {{{ admin tags
class member_admin_tags(member_admin_work_on_selection):

    @with_member_auth(admin_only=True)
    def GET(self):
        members = self.members()
        count_ids_stmt = web.ctx.orm.query(tables.member_tag_table.c.tag_id,
                                           func.count().label("count"),
                                           func.array_to_string(func.array_agg(tables.member_tag_table.c.member_id), ",").label("ids"))\
                                    .group_by(tables.member_tag_table.c.tag_id)
        all = count_ids_stmt.subquery()
        selected = count_ids_stmt.filter(tables.member_tag_table.c.member_id == func.any([member.id for member in members])).subquery()
        photos = web.ctx.orm.query(orm.Photo.tag_id, func.count().label("count")).group_by(orm.Photo.tag_id).subquery()
        tags = web.ctx.orm.query(orm.Tag, all.c.count, all.c.ids, selected.c.count, selected.c.ids, photos.c.count)\
                          .outerjoin((all, orm.Tag.id == all.c.tag_id))\
                          .outerjoin((selected, orm.Tag.id == selected.c.tag_id))\
                          .outerjoin((photos, orm.Tag.id == photos.c.tag_id))\
                          .order_by(orm.Tag.instance_order).all()
        return render.page("/member/admin/tags.html", render.member.admin.tags(tags, members), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        action, = [key for key in web.input().keys() if key != "selection"]
        action, tag = action.split("_")
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join(orm.Instance).filter_by(name=cfg.instance).one()
        members = self.members()
        if action == "add":
            for member in members:
                old = unicode(member)
                member.tags.append(tag)
                new = unicode(member)
                if old != new:
                    web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Mitgliederdaten", member, self.member))
        elif action == "remove":
            for member in members:
                old = unicode(member)
                member.tags.remove(tag)
                new = unicode(member)
                if old != new:
                    web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Mitgliederdaten", member, self.member))
        else:
            raise web.badrequest()
        raise web.seeother("tags.html?selection=%s" % ",".join(str(member.id) for member in members))


class member_admin_tag_form(object):

    def form(self, skip_tag=None):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        tags = [tag for tag in self.instance.tags if skip_tag is None or tag != skip_tag]
        return web.form.Form(web.form.Textbox("name", description="Name"),
                             web.form.Dropdown("pos", [("0", "an erster Position")] +
                                                      [(str(i+1), "nach %s" % tag.name)
                                                       for i, tag in enumerate(tags)], description="Position in der Liste"),
                             web.form.Textbox("description", description="Beschreibung", size=50),
                             web.form.Checkbox("visible", description="sichtbar"),
                             web.form.Textbox("photopath", description="Foto-Verzeichnis", size=50),
                             web.form.Textbox("photographer", description="Fotograf", size=50),
                             web.form.Textbox("labeledphotos", description="beschriftbare Fotos", size=50),
                             web.form.Button("Speichern", type="submit"))


class member_admin_tag_new(member_admin_tag_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        try:
            photopaths = [os.path.normpath(os.path.join(cfg.photopath, dir)) for dir in os.listdir(cfg.photopath)]
        except OSError:
            photopaths = []
        return render.page("/member/admin/tag/new.html", render.member.admin.tag.new(self.form(), photopaths), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        instance = session.query(orm.Instance).filter_by(name=cfg.instance).one()
        try:
            form = self.form()
            if form.validates():
                web.header("Content-Type", "text/plain; charset=utf-8")
                web.header("Transfer-Encoding", "chunked")
                tag = orm.Tag(form.d.name, form.d.description, web.input().has_key("visible"), form.d.photopath, form.d.photographer)
                yield "scanning photos…\n"
                if tag.photopath:
                    for photo in sorted(os.listdir(tag.photopath)):
                        yield "%s: " % photo
                        photo = orm.Photo(photo, tag, photo in form.d.labeledphotos.replace(",", " ").split())
                        session.add(photo)
                        yield "%dx%d (%.1fkB), mid: %dx%d (%.1fkB), thumb: %dx%d (%.1fkB)\n" % (photo.width, photo.height, photo.size/1024.0, photo.midwidth, photo.midheight, photo.midsize/1024.0, photo.thumbwidth, photo.thumbheight, photo.thumbsize/1024.0)
                instance.insert_tag(int(form.d.pos), tag)
                yield "scanning complete.\n"
            else:
                raise web.seeother("../tags.html")
        except web.HTTPError:
            session.commit()
            raise
        except:
            session.rollback()
            raise
        else:
            session.commit()
        session.close()


class member_admin_tag_edit(member_admin_tag_form):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_tag=tag)
        form.name.value = tag.name
        form.description.value = tag.description
        form.visible.checked = tag.visible
        form.photopath.value = tag.photopath
        form.photographer.value = tag.photographer
        form.labeledphotos.value = " ".join(photo.name for photo in tag.photos if photo.allow_labels)
        form.pos.value = str(self.instance.tags.index(tag))
        try:
            photopaths = [os.path.normpath(os.path.join(cfg.photopath, dir)) for dir in os.listdir(cfg.photopath)]
        except OSError:
            photopaths = []
        return render.page("/member/admin/tag/X/edit.html", render.member.admin.tag.edit(form, photopaths), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        instance = session.query(orm.Instance).filter_by(name=cfg.instance).one()
        try:
            tag = session.query(orm.Tag).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
            form = self.form(skip_tag=tag)
            if form.validates():
                web.header("Content-Type", "text/plain; charset=utf-8")
                web.header("Transfer-Encoding", "chunked")
                tag.name = form.d.name
                tag.description = form.d.description
                tag.visible = web.input().has_key("visible")
                tag.photopath = form.d.photopath
                tag.photographer = form.d.photographer
                instance.tags.remove(tag)
                instance.insert_tag(int(form.d.pos), tag)
                photos = dict((photo.name, photo)
                              for photo in session.query(orm.Photo).join(orm.Tag).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance))
                yield "scanning photos…\n"
                if tag.photopath:
                    for photo in sorted(os.listdir(tag.photopath)):
                        yield "%s" % photo
                        if photo in photos:
                            yield " (cached)"
                            photo = photos.pop(photo)
                            photo.allow_labels = photo.name in form.d.labeledphotos.replace(",", " ").split()
                            photo.refresh()
                        else:
                            photo = orm.Photo(photo, tag, photo in form.d.labeledphotos.replace(",", " ").split())
                            session.add(photo)
                        yield ": %dx%d (%.1fkB), mid: %dx%d (%.1fkB), thumb: %dx%d (%.1fkB)\n" % (photo.width, photo.height, photo.size/1024.0, photo.midwidth, photo.midheight, photo.midsize/1024.0, photo.thumbwidth, photo.thumbheight, photo.thumbsize/1024.0)
                for photo in photos:
                    yield "remove spurious photo %s\n" % photo
                    session.delete(photos[photo]) # fails, if labels are present -> feature.
                yield "scanning complete.\n"
            else:
                raise web.seeother("../../tags.html")
        except web.HTTPError:
            session.commit()
            raise
        except:
            session.rollback()
            raise
        else:
            session.commit()
        session.close()


class member_admin_tag_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/tag/X/delete.html", render.member.admin.tag.delete(tag), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        web.ctx.orm.delete(tag)
        raise web.seeother("../../tags.html")
# }}} admin tags

# {{{ admin circulars
class member_admin_circulars(member_admin_work_on_selection):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("circular", [(circular.id, circular.title) for circular in self.instance.circulars], description="Chorbrief"),
                             web.form.Dropdown("action", [("new:none", "neu einstellen und als ungelesen markieren"),
                                                          ("new:online", "neu einstellen und als online gelesen markieren"),
                                                          ("new:snailmail", "neu einstellen und als Brief gelesen marieren"),
                                                          ("change:none", "als ungelesen markieren"),
                                                          ("change:online", "als online gelesen markieren"),
                                                          ("change:snailmail", "als Brief gelesen marieren"),
                                                          ("delete", "entfernen")], description="Aktion"),
                             web.form.Hidden("selection"),
                             web.form.Button("Ausführen", type="submit"))

    @with_member_auth(admin_only=True)
    def GET(self):
        members = self.members()
        count_ids_stmt = web.ctx.orm.query(orm.Message.circular_id,
                                           func.count().label("count"),
                                           func.array_to_string(func.array_agg(orm.Message.member_id), ",").label("ids"))\
                                    .group_by(orm.Message.circular_id)
        total = count_ids_stmt.subquery()
        total_selected = count_ids_stmt.filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        unread = count_ids_stmt.filter_by(access_by=None).subquery()
        unread_selected = count_ids_stmt.filter_by(access_by=None).filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        online = count_ids_stmt.filter_by(access_by=u'online').subquery()
        online_selected = count_ids_stmt.filter_by(access_by=u'online').filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        snailmail = count_ids_stmt.filter_by(access_by=u'snailmail').subquery()
        snailmail_selected = count_ids_stmt.filter_by(access_by=u'snailmail').filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        circulars = web.ctx.orm.query(orm.Circular,
                                      total.c.count, total.c.ids,
                                      total_selected.c.count, total_selected.c.ids,
                                      unread.c.count, unread.c.ids,
                                      unread_selected.c.count, unread_selected.c.ids,
                                      online.c.count, online.c.ids,
                                      online_selected.c.count, online_selected.c.ids,
                                      snailmail.c.count, snailmail.c.ids,
                                      snailmail_selected.c.count, snailmail_selected.c.ids)\
                               .outerjoin((total, orm.Circular.id == total.c.circular_id))\
                               .outerjoin((total_selected, orm.Circular.id == total_selected.c.circular_id))\
                               .outerjoin((unread, orm.Circular.id == unread.c.circular_id))\
                               .outerjoin((unread_selected, orm.Circular.id == unread_selected.c.circular_id))\
                               .outerjoin((online, orm.Circular.id == online.c.circular_id))\
                               .outerjoin((online_selected, orm.Circular.id == online_selected.c.circular_id))\
                               .outerjoin((snailmail, orm.Circular.id == snailmail.c.circular_id))\
                               .outerjoin((snailmail_selected, orm.Circular.id == snailmail_selected.c.circular_id))\
                               .order_by(orm.Circular.instance_order).all()
        form = self.form()
        form.selection.value = ",".join([str(member.id) for member in members])
        return render.page("/member/admin/circulars.html", render.member.admin.circulars(form, circulars, members), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(form.d.circular)).join(orm.Instance).filter_by(name=cfg.instance).one()
            members = self.members()
            action = form.d.action.split(":")[0]
            if action != "delete":
                access_by = form.d.action.split(":", 1)[1]
                if access_by == "none":
                    access_by = None
            if action == "new":
                for member in members:
                    web.ctx.orm.add(orm.Message(member, circular, access_by))
            elif action == "change":
                for member in members:
                    message = web.ctx.orm.query(orm.Message).filter_by(member_id=member.id).filter_by(circular_id=circular.id).one()
                    message.access_by = access_by
                    if access_by:
                        message.access_when = datetime.datetime.now()
                    else:
                        message.access_when = None
            elif action == "delete":
                for member in members:
                    message = web.ctx.orm.query(orm.Message).filter_by(member_id=member.id).filter_by(circular_id=circular.id).one()
                    web.ctx.orm.delete(message)
            else:
                raise web.badrequest()
            raise web.seeother("circulars.html?selection=%s" % ",".join(str(member.id) for member in members))


class member_admin_circular_copy(object):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("circular", [("0", "(neuen leeren Chorbrief anlegen)")] +
                                                           [(circular.id, circular.title)
                                                            for circular in self.instance.circulars], description="Inhalt von altem Chorbrief kopieren"),
                             web.form.Button("Ausführen", type="submit"))

    @with_member_auth(admin_only=True)
    def GET(self):
        return render.page("/member/admin/circular/copy.html", render.member.admin.circular.copy(self.form()), self.member)


class member_admin_circular_form(object):

    def form(self, skip_circular=None):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        circulars = [circular for circular in self.instance.circulars if skip_circular is None or circular != skip_circular]
        return web.form.Form(web.form.Textbox("name", description=u"Name (für url etc.)", size=50),
                             web.form.Textbox("title", description="Titel", size=50),
                             web.form.Dropdown("pos", [("0", "an erster Position")] +
                                                      [(str(i+1), "nach %s" % circular.title)
                                                       for i, circular in enumerate(circulars)], description="Position in der Liste"),
                             web.form.Textarea("html", description="HTML", cols=80, rows=40),
                             web.form.Textarea("email", description="E-Mail", cols=80, rows=40),
                             web.form.Button("Speichern", type="submit"))


class member_admin_circular_new(member_admin_circular_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        try:
            id = int(web.input().get("circular"))
            circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        except:
            pass
        else:
            form.name.value = circular.name
            form.title.value = circular.title
            form.html.value = circular.html
            form.email.value = circular.email
        return render.page("/member/admin/circular/new.html", render.member.admin.circular.new(form), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            circular = orm.Circular(form.d.name, form.d.title, form.d.html, form.d.email)
            self.instance.insert_circular(int(form.d.pos), circular)
            raise web.seeother("../circulars.html")
        else:
            return render.page("/member/admin/circular/new.html", render.member.admin.circular.new(form), self.member)


class member_admin_circular_edit(member_admin_circular_form):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_circular=circular)
        form.name.value = circular.name
        form.title.value = circular.title
        form.html.value = circular.html
        form.email.value = circular.email
        form.pos.value = str(self.instance.circulars.index(circular))
        return render.page("/member/admin/circular/X/edit.html", render.member.admin.circular.edit(form), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_circular=circular)
        if form.validates():
            circular.name = form.d.name
            circular.title = form.d.title
            circular.html = form.d.html
            circular.email = form.d.email
            self.instance.circulars.remove(circular)
            self.instance.insert_circular(int(form.d.pos), circular)
            raise web.seeother("../../circulars.html")
        else:
            return render.page("/member/admin/circular/X/edit.html", render.member.admin.circular.edit(form), self.member)


class member_admin_circular_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/circular/X/delete.html", render.member.admin.circular.delete(circular), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        for message in circular.messages:
            web.ctx.orm.delete(message)
        web.ctx.orm.delete(circular)
        raise web.seeother("../../circulars.html")


class member_admin_attachments(object):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/circular/X/attachments.html", render.member.admin.circular.attachments(circular), self.member)


class member_admin_attachment_form(object):

    def form(self, skip_attachment=None):
        attachments = [attachment for attachment in self.circular.attachments if skip_attachment is None or attachment != skip_attachment]
        return web.form.Form(web.form.Textbox("name", description="Dateiname", size=50),
                             web.form.Dropdown("mimetype", [(attachment.mime, attachment.type)
                                                            for attachment in cfg.attachments], description="Dateityp"),
                             web.form.File("data", description="Datei"),
                             web.form.Dropdown("pos", [("0", "an erster Position")] +
                                                      [(str(i+1), "nach %s" % attachment.name)
                                                       for i, attachment in enumerate(attachments)], description="Position in der Liste"),
                             web.form.Button("Speichern", type="submit"))


class member_admin_attachment_show(member_admin_attachment_form):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id, attachment_id):
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        web.header("Content-Type", attachment.mimetype)
        web.header("Content-Disposition", "attachment; filename=%s" % attachment.name)
        return attachment.data


class member_admin_attachment_new(member_admin_attachment_form):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form()
        return render.page("/member/admin/circular/X/attachment/new.html", render.member.admin.circular.attachment.new(form, self.circular), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, circular_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form()
        if form.validates():
            attachment = orm.Attachment(form.d.name, form.d.mimetype, form.d.data)
            self.circular.insert_attachment(int(form.d.pos), attachment)
            raise web.seeother("../attachments.html")
        else:
            return render.page("/member/admin/circular/X/attachment/new.html", render.member.admin.circular.attachment.new(form, self.circular), self.member)


class member_admin_attachment_edit(member_admin_attachment_form):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id, attachment_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_attachment=attachment)
        form.name.value = attachment.name
        form.mimetype.value = attachment.mimetype
        form.pos.value = str(self.circular.attachments.index(attachment))
        return render.page("/member/admin/circular/X/attachment/X/edit.html", render.member.admin.circular.attachment.edit(form, attachment), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, circular_id, attachment_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_attachment=attachment)
        if form.validates():
            attachment.name = form.d.name
            attachment.mimetype = form.d.mimetype
            if form.d.data:
                attachment.data = form.d.data
            self.circular.attachments.remove(attachment)
            self.circular.insert_attachment(int(form.d.pos), attachment)
            raise web.seeother("../../attachments.html")
        else:
            return render.page("/member/admin/circular/X/attachment/X/edit.html", render.member.admin.circular.attachment.edit(form, attachment), self.member)


class member_admin_attachment_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id, attachment_id):
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/circular/X/attachment/X/delete.html", render.member.admin.circular.attachment.delete(attachment), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, circular_id, attachment_id):
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        web.ctx.orm.delete(attachment)
        raise web.seeother("../../attachments.html")
# }}} admin circulars

# {{{ admin links
class member_admin_links(member_admin_work_on_selection):

    @with_member_auth(admin_only=True)
    def GET(self):
        members = self.members()
        count_ids_stmt = web.ctx.orm.query(orm.Link.entrance_id,
                                           func.count().label("count"),
                                           func.array_to_string(func.array_agg(orm.Link.member_id), ",").label("ids"))\
                                    .group_by(orm.Link.entrance_id)
        all = count_ids_stmt.subquery()
        selected = count_ids_stmt.filter(orm.Link.member_id == func.any([member.id for member in members])).subquery()
        entrances = web.ctx.orm.query(orm.Entrance, all.c.count, all.c.ids, selected.c.count, selected.c.ids)\
                               .outerjoin((all, orm.Entrance.id == all.c.entrance_id))\
                               .outerjoin((selected, orm.Entrance.id == selected.c.entrance_id))\
                               .order_by(orm.Entrance.instance_order).all()
        return render.page("/member/admin/links.html", render.member.admin.links(entrances, members), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        action, = [key for key in web.input().keys() if key != "selection"]
        action, entrance = action.split("_")
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(entrance)).join(orm.Instance).filter_by(name=cfg.instance).one()
        members = self.members()
        if action == "add":
            for member in members:
                web.ctx.orm.add(orm.Link(unicode(uuid.uuid4()), member, entrance))
        elif action == "remove":
            for member in members:
                member.entrances.remove(entrance)
        elif action == "email":
            raise web.seeother("link/%i/email.html?selection=%s" % (entrance.id, ",".join(str(member.id) for member in members)))
        else:
            raise web.badrequest()
        raise web.seeother("links.html?selection=%s" % ",".join(str(member.id) for member in members))


def get_expire(i):
    if not i.expire:
        return True
    day, month, year = map(int, i.expire.split("."))
    return datetime.date(year, month, day)


class member_admin_link_form(object):

    def form(self, skip_entrance=None):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        entrances = [entrance for entrance in self.instance.entrances if skip_entrance is None or entrance != skip_entrance]
        return web.form.Form(web.form.Textbox("url", description="redirect to", size=50),
                             web.form.Textbox("expire", description="gültig bis TT.MM.JJJJ"),
                             web.form.Dropdown("pos", [("0", "an erster Position")] +
                                                      [(str(i+1), "nach %s vom %s" % (entrance.url, entrance.expire.strftime("%d.%m.%Y")))
                                                       for i, entrance in enumerate(entrances)], description="Position in der Liste"),
                             web.form.Button("Speichern", type="submit"),
                             validators = [web.form.Validator("Ungültiges Ablaufdatum.", get_expire)])


class member_admin_link_new(member_admin_link_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        entrance = web.ctx.orm.query(orm.Entrance).join(orm.Instance).filter_by(name=cfg.instance).order_by([desc(orm.Entrance.expire)]).limit(1).all()
        if entrance:
            form.expire.value = entrance[0].expire.strftime("%d.%m.%Y")
        return render.page("/member/admin/link/new.html", render.member.admin.link.new(form, self.instance), self.member)

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            entrance = orm.Entrance(form.d.url, get_expire(form.d))
            self.instance.insert_entrance(int(form.d.pos), entrance)
            raise web.seeother("../links.html")
        else:
            return render.page("/member/admin/link/new.html", render.member.admin.link.new(form, self.instance), self.member)


class member_admin_link_edit(member_admin_link_form):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_entrance=entrance)
        form.url.value = entrance.url
        form.expire.value = entrance.expire.strftime("%d.%m.%Y")
        form.pos.value = str(self.instance.entrances.index(entrance))
        return render.page("/member/admin/link/X/edit.html", render.member.admin.link.edit(form, self.instance), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_entrance=entrance)
        if form.validates():
            entrance.url = form.d.url
            entrance.expire = get_expire(form.d)
            self.instance.entrances.remove(entrance)
            self.instance.insert_entrance(int(form.d.pos), entrance)
            raise web.seeother("../../links.html")
        else:
            return render.page("/member/admin/link/X/edit.html", render.member.admin.link.edit(form, self.instance), self.member)


class member_admin_link_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/link/X/delete.html", render.member.admin.link.delete(entrance), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        for link in entrance.links:
            web.ctx.orm.delete(link)
        web.ctx.orm.delete(entrance)
        raise web.seeother("../../links.html")


class member_admin_link_email(member_admin_work_on_selection):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("circular", [(str(circular.id), "%s vom %s" % (circular.title, circular.created.strftime("%d.%m.%Y")) if circular.id != 1 else circular.title)
                                                            for circular in self.instance.circulars], description="E-Mail-Text"),
                             web.form.Hidden("selection"),
                             web.form.Button("Versenden", type="submit"))

    @with_member_auth(admin_only=True)
    def GET(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        if web.input().get("selection") is not None:
            members = self.members()
        else:
            members = entrance.members
        missing = [member for member in members if not member.email]
        members = [member for member in members if member.email]
        form = self.form()
        form.selection.value = ",".join([str(member.id) for member in members])
        return render.page("/member/admin/link/X/email.html", render.member.admin.link.email(form, entrance, members, missing), self.member)

    @with_member_auth(admin_only=True)
    def POST(self, id):
        form = self.form()
        if form.validates():
            session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
            web.header("Content-Type", "text/plain; charset=utf-8")
            web.header("Transfer-Encoding", "chunked")
            members = self.members()
            yield "sending %i emails…\n" % len(members)
            s = smtplib.SMTP()
            s.connect()
            entrance = session.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
            circular = session.query(orm.Circular).filter_by(id=int(form.d.circular)).join(orm.Instance).filter_by(name=cfg.instance).one()
            for i, member in enumerate(members):
                link = web.ctx.orm.query(orm.Link).join(orm.Entrance).filter_by(id=entrance.id).join(orm.Member).filter_by(id=member.id).one()
                body = circular.email % {"firstname": member.firstname, "lastname": member.lastname, "uuid": link.uuid}
                if not circular.attachments:
                    msg = email.MIMEText.MIMEText(body.encode("utf-8"), _charset="utf-8")
                else:
                    msg = email.MIMEMultipart.MIMEMultipart()
                    msg.attach(email.MIMEText.MIMEText(("%s\n" % body).encode("utf-8"), _charset="utf-8"))
                    for attachment in circular.attachments:
                        attachment_msg = email.MIMEBase.MIMEBase(*attachment.mimetype.split("/"))
                        attachment_msg.set_payload(attachment.data)
                        email.Encoders.encode_base64(attachment_msg)
                        attachment_msg.add_header("Content-Disposition", "attachment", filename=attachment.name)
                        msg.attach(attachment_msg)
                msg["Subject"] = circular.title
                msg["From"] = cfg.from_email
                to_emails = member.email.split(",")
                msg["To"] = to_emails[0]
                if len(to_emails) > 1:
                    msg["Cc"] = ",".join(to_emails[1:])
                msg["Date"] = email.Utils.formatdate(localtime=True)
                yield "%i: %s\n" % (i+1, to_emails[0])
                s.sendmail(cfg.from_email, to_emails, msg.as_string())
            s.close()
            yield "complete.\n"
            session.close()
        else:
            raise web.seeother("../../links.html")


# }}} admin links
# }}} admin

if path.endswith("/dev"):
    if __name__ == "__main__":
        print "socmanager  Copyright (C) 2010  André Wobst"
        app.run()
else:
    application = app.wsgifunc()

# vim:fdm=marker
