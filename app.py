# -*- encoding: utf-8 -*-
#
# socmanager, http://code.google.com/p/socmanager/
# Copyright (C) 2010-2011  André Wobst
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
cgi.maxlen = 10 * 1024 * 1024 # 1 MB limit for POST data
emailPattern = re.compile(r"[a-zA-Z0-9\!\#\$\%\&\\\"\*\=\?\^\'\(\)\|\~\_\-\.\+\/]+@([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,4}$")

import email.Charset, email.MIMEText, email.MIMEMultipart, email.MIMEBase, email.Utils, smtplib
email.Charset.add_charset("utf-8", email.Charset.SHORTEST, None, None)

from PIL import Image, ImageDraw

try:
    import json
except ImportError:
    import simplejson as json
import web

from sqlalchemy import create_engine, func, Integer, and_, or_, select
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc

import orm, tables, iban

class socRadio(web.form.Radio):

    def render(self):
        x = '<span>'
        for arg in self.args:
            if isinstance(arg, (tuple, list)):
                value, desc= arg
            else:
                value, desc = arg, arg
            attrs = self.attrs.copy()
            attrs['name'] = self.name
            attrs['type'] = 'radio'
            attrs['value'] = value
            attrs['id'] += '_' + value
            if self.value == value:
                attrs['checked'] = 'checked'
            x += '<input %s/> <label for="%s">%s</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' % (attrs, attrs['id'], web.net.websafe(desc))
        x += '</span>'
        return x


urls = ("/login.html$", "login",
        "/logout.html$", "logout",
        "/link.html$", "link",
        "/tickets.html$", "tickets",
        "/tickets.png$", "ticketsmap",
        "/tickets_ok_([^.]+).html$", "tickets_ok",
        "/newsletter.html$", "newsletter",
        "(|/member|/member/photos)$", "add_slash",
        "/(press|press/|press/[a-z]+\.html)$", "press_redirect",
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
        "/member/admin/member/(\d+)/clearpasswd.html$", "member_admin_member_clearpasswd",
        "/member/admin/member/(\d+)/changes.html$", "member_admin_member_changes",
        "/member/admin/print.html$", "member_admin_print",
        "/member/admin/tags.html$", "member_admin_tags",
        "/member/admin/tag/new.html$", "member_admin_tag_new",
        "/member/admin/tag/(\d+)/edit.html$", "member_admin_tag_edit",
        "/member/admin/tag/(\d+)/delete.html$", "member_admin_tag_delete",
        "/member/admin/tickets/(\d+)/index.html$", "member_admin_tickets",
        "/member/admin/tickets/(\d+)/map.png$", "member_admin_ticketmappng",
        "/member/admin/tickets/(\d+)/map.pdf$", "member_admin_ticketmappdf",
        "/member/admin/tickets/(\d+)/map.html$", "member_admin_tickets_map",
        "/member/admin/tickets/(\d+)/coupon.html$", "member_admin_tickets_coupon",
        "/member/admin/tickets/(\d+)/coupons.pdf$", "member_admin_tickets_couponspdf",
        "/member/admin/tickets/(\d+)/newsletter.html$", "member_admin_tickets_newsletter",
        "/member/admin/tickets/(\d+)/clean.html$", "member_admin_tickets_clean",
        "/member/admin/tickets/(\d+)/new.html$", "member_admin_tickets_new",
        "/member/admin/tickets/(\d+)/sold/(\d+)/edit.html$", "member_admin_tickets_edit",
        "/member/admin/tickets/(\d+)/sold/(\d+)/pay.html$", "member_admin_tickets_pay",
        "/member/admin/tickets/(\d+)/sold/([\d,]+)/pickup.html$", "member_admin_tickets_pickup",
        "/member/admin/tickets/(\d+)/sold/(\d+)/remind.html$", "member_admin_tickets_remind",
        "/member/admin/tickets/(\d+)/sold/(\d+)/delete.html$", "member_admin_tickets_delete",
        "/member/admin/tickets/(\d+)/debit.html$", "member_admin_tickets_debit",
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


web.config.debug = False
app = web.application(urls, locals())
app.add_processor(load_sqla)

render = web.template.render(os.path.join(path, "templates"), globals={"str": str, "sorted": sorted, "sum": sum})

def ticket_sale_open():
    instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
    return instance.onsale and not instance.sale_temporarily_closed

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
                          web.form.Button("submit", type="submit", html=u"Login"))

class login(object):

    def GET(self):
        form = LoginForm()
        form.validates()
        press = form.d.next and form.d.next.startswith("/member/wiki/press/")
        return render.page("/login.html", render.login(form, press=press), None, ticket_sale_open())

    def POST(self):
        form = LoginForm()
        form.validates()
        if form.d.login:
            try:
                member = web.ctx.orm.query(orm.Member).filter_by(login=form.d.login).one()
            except NoResultFound:
                time.sleep(1)
                return render.page("/login.html", render.login(form, failed=True), None, ticket_sale_open())
            if hashlib.md5((u"%s%s" % (member.salt, form.d.passwd)).encode("utf-8")).hexdigest() != member.passwd:
                time.sleep(1)
                return render.page("/login.html", render.login(form, failed=True), None, ticket_sale_open())
            salt = os.urandom(16).encode("hex")
            hash = hashlib.md5(("".join([cfg.secret, salt, str(member.id)])).encode("utf-8")).hexdigest()
            web.setcookie(cfg.cookie, " ".join([hash, salt, str(member.id)]), 86400)
            if form.d.next and form.d.next.find(":") == -1 and form.d.next.lower().find("%3a") == -1:
                raise web.seeother(form.d.next)
            raise web.seeother("/member/index.html")
        return render.page("/login.html", render.login(form), None, ticket_sale_open())


class logout(object):

    def POST(self):
        web.setcookie(cfg.cookie, "", -1)
        return render.page("/logout.html", render.logout(), None, ticket_sale_open())


class link(object):

    def GET(self):
        try:
            link = web.ctx.orm.query(orm.Link).filter_by(uuid=web.input().get("uuid", "")).one()
        except NoResultFound:
            return render.page("/login.html", render.login(LoginForm(), failed=True), None, ticket_sale_open())
        if datetime.date.today() > link.entrance.expire:
            return render.page("/login.html", render.login(LoginForm(), failed=True), None, ticket_sale_open())
        salt = os.urandom(16).encode("hex")
        hash = hashlib.md5(("".join([cfg.secret, salt, str(link.member.id)])).encode("utf-8")).hexdigest()
        web.setcookie(cfg.cookie, " ".join([hash, salt, str(link.member.id)]), 86400)
        raise web.seeother(link.entrance.url)


class add_slash(object):

    def GET(self, path):
        raise web.seeother("%s/" % path)


class press_redirect(object):

    def GET(self, path):
        if path in ["press", "press/", "press/index.html"]:
            raise web.seeother("/press.html")
        else:
            raise web.seeother("/login.html?%s" % (urllib.urlencode({"next": "member/wiki/%s" % path[:-5]})))


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
                (admin_only and u"admin" not in [tag.name for tag in self.member.tags]) or
                (active_only and u"inaktiv" in [tag.name for tag in self.member.tags])):
                raise web.seeother("/login.html?%s" % (urllib.urlencode({"next": web.ctx.path})))
            return f(self, *args, **kwargs)
        return wrapper
    return with_member_info


class pages(object):

    @with_member_info
    def GET(self, path):
        if path in ["page.html", "tickets_pay.html", "tickets_pickup.html"]:
            raise web.NotFound()
        if not path:
            path = "index.html"
        if not path.endswith(".html"):
            raise web.NotFound()
        try:
            content = getattr(render, path[:-5])
        except AttributeError:
            raise web.NotFound()
        return render.page("/%s" % path, content(), self.member, ticket_sale_open())


class ticketsmap(object):

    def GET(self):
        instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        if not instance.onsale:
            raise web.NotFound()
        selected = web.input().get("selected")
        if selected:
            selected = map(int, selected.split(','))
        else:
            selected = []
        sold = web.input().get("sold")
        if sold:
            sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=instance.onsale.id).one()
        i = ticketmap(instance.onsale, include_wheelchair_only=sold is not None, selected=selected, sold=sold)
        web.header("Content-Type", "image/png")
        web.header("Cache-Control", "no-cache, must-revalidate")
        return i


class ticket_form(object):

    def ticket_form(self, tag, banktransfer, shipment):
        return web.form.Form(web.form.Dropdown("gender", [("female", "Frau"), ("male", "Herr")], description="Anrede"),
                             web.form.Textbox("name", notnull, description=u"Nachname", size=50),
                             web.form.Textbox("email", notnull, description="E-Mail", size=50),
                             web.form.Textbox("coupon", description="Gutschein", size=50),
                             web.form.Checkbox("newsletter", description="Rundschreiben", value="yes"),
                             socRadio("payment", ([("banktransfer", u"Überweisung")] if banktransfer else []) + [("debit", "Lastschrift")], description="Zahlungsweise"),
                             web.form.Textbox("account_holder", description="Kontoinhaber", size=50),
                             web.form.Textbox("account_iban", description="IBAN", size=50),
                             web.form.Textbox("account_bic", description="BIC", size=50),
                             *(([web.form.Checkbox("with_shipment", description="Versand (zzgl. 1€)", value="yes"),
                                 web.form.Textbox("shipment_firstname", description="Vorname", size=50),
                                 web.form.Textbox("shipment_surname", description="Nachname", size=50),
                                 web.form.Textbox("shipment_street", description="Straße und Nr.", size=50),
                                 web.form.Textbox("shipment_zip", description="PLZ", size=50),
                                 web.form.Textbox("shipment_city", description="Ort", size=50)] if shipment else []
                                ) + [
                                 web.form.Hidden("selected"),
                                 web.form.Button("submit", type="submit", html=u"Karten verbindlich kaufen"),
                                ]),
                             validators = [web.form.Validator("Formatfehler in E-Mail-Adresse(n).", checkemail),
                                           web.form.Validator("Ungültiger Gutschein.", checkcoupon(tag)),
                                           web.form.Validator("Ungültige Zahlungsangaben.", checkaccount),
                                           web.form.Validator("Ungültige Versandangaben.", checkshipment)])

    def newsletter_form(self):
        return web.form.Form(web.form.Dropdown("gender", [("female", "Frau"), ("male", "Herr")], description="Anrede"),
                             web.form.Textbox("name", notnull, description=u"Nachname", size=50),
                             web.form.Textbox("email", notnull, description="E-Mail", size=50),
                             web.form.Button("submit", type="submit", html=u"Rundschreiben abonnieren"),
                             validators = [web.form.Validator("Formatfehler in E-Mail-Adresse(n).", checkemail)])

class tickets(ticket_form):

    @with_member_info
    def GET(self):
        instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        if not instance.onsale:
            newsletter_form = self.newsletter_form()
            return render.page("/tickets.html", render.tickets_info(newsletter_form), self.member, ticket_sale_open())
        if instance.sale_temporarily_closed:
            return render.page("/tickets.html", render.tickets_closed(), self.member, ticket_sale_open())
        ticket_form = self.ticket_form(instance.onsale, instance.bank_transfer_possible, instance.shipment_possible)
        if not instance.bank_transfer_possible:
            ticket_form.payment.value = 'debit'
        return render.page("/tickets.html", render.tickets(ticket_form, instance.onsale, []), self.member, ticket_sale_open())

    @with_member_info
    def POST(self):
        instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        if not instance.onsale:
            newsletter_form = self.newsletter_form()
            return render.page("/tickets_info.html", render.tickets_info(newsletter_form), self.member, ticket_sale_open())
        if instance.sale_temporarily_closed:
            return render.page("/tickets_closed.html", render.tickets_closed(), self.member, ticket_sale_open())
        ticket_form = self.ticket_form(instance.onsale, instance.bank_transfer_possible, instance.shipment_possible)
        x = web.input().get("map.x")
        y = web.input().get("map.y")
        clicked = None
        if x and y:
            zoom = web.input().get("zoom", "1")
            x = int(float(x)/float(zoom))
            y = int(float(y)/float(zoom))
            clicked = web.ctx.orm.query(orm.Ticket).filter_by(tag_id=instance.onsale.id).filter(orm.Ticket.left<x).filter(orm.Ticket.right>x).filter(orm.Ticket.top<y).filter(orm.Ticket.bottom>y).first()
        if ticket_form.validates() and x is None and y is None and ticket_form.d.selected:
            if instance.shipment_possible:
                sold = orm.Sold(gender=ticket_form.d.gender, name=ticket_form.d.name, email=ticket_form.d.email, online=True, payment=ticket_form.d.payment, account_holder=ticket_form.d.account_holder, account_iban=ticket_form.d.account_iban.replace(' ', ''), account_bic=ticket_form.d.account_bic.strip(), tag=instance.onsale, shipment=web.input().has_key("with_shipment"), shipment_firstname=ticket_form.d.shipment_firstname, shipment_surname=ticket_form.d.shipment_surname, shipment_street=ticket_form.d.shipment_street, shipment_zip=ticket_form.d.shipment_zip, shipment_city=ticket_form.d.shipment_city)
            else:
                sold = orm.Sold(gender=ticket_form.d.gender, name=ticket_form.d.name, email=ticket_form.d.email, online=True, payment=ticket_form.d.payment, account_holder=ticket_form.d.account_holder, account_iban=ticket_form.d.account_iban.replace(' ', ''), account_bic=ticket_form.d.account_bic.strip(), tag=instance.onsale)
            if web.input().has_key("newsletter"):
                web.ctx.orm.query(orm.Newsletter).filter_by(email=ticket_form.d.email).delete()
                orm.Newsletter(ticket_form.d.gender, ticket_form.d.name, ticket_form.d.email, instance)
            web.ctx.orm.add(sold)
            web.ctx.orm.commit()
            selected = map(int, ticket_form.d.selected.split(","))
            for ticket_id in selected:
                web.ctx.orm.query(orm.Ticket).filter_by(tag_id=instance.onsale.id).filter_by(id=ticket_id).filter_by(sold_id=None).update({"sold_id": sold.id})
                web.ctx.orm.commit()
                if not web.ctx.orm.query(orm.Ticket).filter_by(tag_id=instance.onsale.id).filter_by(id=int(ticket_id)).filter_by(sold_id=sold.id).first():
                    web.ctx.orm.query(orm.Ticket).filter_by(sold_id=sold.id).update({"sold_id": None})
                    web.ctx.orm.delete(sold)
                    ticket_form.selected.value = ""
                    return render.page("/tickets.html", render.tickets(ticket_form, instance.onsale, [], failed=True), self.member, ticket_sale_open())
            if ticket_form.d.coupon:
                web.ctx.orm.commit()
                for coupon in ticket_form.d.coupon.split(","):
                    coupon_id, code = coupon.split("-")
                    coupon_id = int(coupon_id)
                    web.ctx.orm.query(orm.Coupon).filter_by(tag_id=instance.onsale.id).filter_by(id=coupon_id).filter_by(code=code).filter_by(sold_id=None).update({"sold_id": sold.id})
            amount = sum(ticket.regular for ticket in sold.tickets)-sum(coupon.amount for coupon in sold.coupons)
            if sold.shipment:
                amount += 1
            if amount <= 0:
                sold.payed = datetime.datetime.now()
                sold.payment = 'coupon'
            web.ctx.orm.commit()
            s = smtplib.SMTP()
            s.connect()
            if amount > 0:
                if ticket_form.d.payment == 'banktransfer':
                    if sold.shipment:
                        msg = email.MIMEText.MIMEText(unicode(render.tickets_pay_shipment(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                        msg["Subject"] = u"Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
                    else:
                        msg = email.MIMEText.MIMEText(unicode(render.tickets_pay(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                        msg["Subject"] = u"Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
                else:
                    if sold.shipment:
                        msg = email.MIMEText.MIMEText(unicode(render.tickets_debit_shipment(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                        msg["Subject"] = u"Lastschriftmandat für Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
                    else:
                        msg = email.MIMEText.MIMEText(unicode(render.tickets_debit(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                        msg["Subject"] = u"Abholkennwort und Lastschriftmandat für Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
            else:
                if sold.shipment:
                    msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_payed_shipment(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                    msg["Subject"] = u"Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
                else:
                    msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_payed(instance.onsale, sold)).encode("utf-8"), _charset="utf-8")
                    msg["Subject"] = u"Abholkennwort für Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
            msg["From"] = cfg.from_email
            to_emails = sold.email.split(",")
            msg["To"] = to_emails[0]
            if len(to_emails) > 1:
                msg["Cc"] = ",".join(to_emails[1:])
            msg["Date"] = email.Utils.formatdate(localtime=True)
            to_emails.append(cfg.from_email)
            s.sendmail(cfg.from_email, to_emails, msg.as_string())
            s.close()
            raise web.seeother("tickets_ok_%s.html" % hashlib.md5(("-".join([cfg.secret, str(sold.id), sold.bankcode, sold.pickupcode])).encode("utf-8")).hexdigest())
        else:
            if ticket_form.d.selected:
                selected = set(map(int, ticket_form.d.selected.split(",")))
            else:
                selected = set()
            if clicked:
                if clicked.id in selected:
                    selected.remove(clicked.id)
                elif not clicked.sold_id:
                    selected.add(clicked.id)
            selected = list(selected)
            selected.sort()
            tickets = [web.ctx.orm.query(orm.Ticket).filter_by(tag_id=instance.onsale.id).filter_by(id=ticket_id).first()
                       for ticket_id in selected]
            ticket_form.selected.value = ",".join(map(str, selected))
            return render.page("/tickets.html", render.tickets(ticket_form, instance.onsale, tickets, formerror=x is None and y is None), self.member, ticket_sale_open())


class tickets_ok(object):

    @with_member_info
    def GET(self, hash):
        printview = web.ctx.method=="POST"
        for sold in web.ctx.orm.query(orm.Sold):
            if hash == hashlib.md5(("-".join([cfg.secret, str(sold.id), sold.bankcode, sold.pickupcode])).encode("utf-8")).hexdigest():
                amount = sum(ticket.regular for ticket in sold.tickets)-sum(coupon.amount for coupon in sold.coupons)
                if amount > 0:
                    if sold.payment == 'banktransfer':
                        if sold.shipment:
                            content = render.tickets_ok_shipment
                        else:
                            content = render.tickets_ok
                    else:
                        if sold.shipment:
                            content = render.tickets_debitonline_shipment
                        else:
                            content = render.tickets_debitonline
                else:
                    if sold.shipment:
                        content = render.tickets_free_shipment
                    else:
                        content = render.tickets_free
                return render.page("/tickets_ok_%s.html" % hash, content(sold.tag, sold, printview, hash), self.member, ticket_sale_open(), printview=printview)
        raise web.NotFound()

    POST=GET


class newsletter(ticket_form):

    @with_member_info
    def GET(self):
        remove = web.input().get("remove", "")
        if remove:
            return render.page("/newsletter.html", render.newsletter_remove(remove), self.member, ticket_sale_open())
        newsletter_form = self.newsletter_form()
        return render.page("/newsletter.html", render.newsletter(newsletter_form), self.member, ticket_sale_open())

    @with_member_info
    def POST(self):
        remove = web.input().get("remove", "")
        if remove:
            web.ctx.orm.query(orm.Newsletter).filter_by(email=remove).delete()
            return render.page("/newsletter_removed.html", render.newsletter_removed(), self.member, ticket_sale_open())
        newsletter_form = self.newsletter_form()
        if newsletter_form.validates():
            instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
            web.ctx.orm.query(orm.Newsletter).filter_by(email=newsletter_form.d.email).delete()
            orm.Newsletter(newsletter_form.d.gender, newsletter_form.d.name, newsletter_form.d.email, instance)
            return render.page("/newsletter_ok.html", render.newsletter_ok(), self.member, ticket_sale_open())
        return render.page("/newsletter.html", render.newsletter(newsletter_form), self.member, ticket_sale_open())

# }}} public

# {{{ member
class member(object):

    @with_member_auth()
    def GET(self, path):
        if not path:
            path = "index.html"
        if path == "index.html":
            new_circulars = web.ctx.orm.query(orm.Circular).join(orm.Message).filter_by(member_id=self.member.id).filter(orm.Message.access_by == None).order_by(orm.Circular.instance_order).all()
            old_circulars = web.ctx.orm.query(orm.Circular).join(orm.Message).filter_by(member_id=self.member.id).filter(orm.Message.access_by != None).order_by(orm.Circular.instance_order).all()
            return render.page("/member/%s" % path, getattr(render.member, path[:-5])(self.member, new_circulars, old_circulars), self.member, ticket_sale_open())
        else:
            return render.page("/member/%s" % path, getattr(render.member, path[:-5])(self.member), self.member, ticket_sale_open())


notnull = web.form.Validator("Notwendige Angabe", bool)

def checkemail(i):
    if not i.email:
        return True
    for email in i.email.split(","):
        if not emailPattern.match(email):
            return False
    return True


def checkcoupon(tag, sold=None):
    coupons = set('%i-%s' % (coupon.id, coupon.code) for coupon in tag.coupons if not coupon.sold_id or (sold and sold == coupon.sold))
    def _checkcoupon(i):
        if not i.coupon:
            return True
        for coupon in i.coupon.split(","):
            coupon = coupon.replace(" ", "")
            coupons.remove(coupon)
        return True
    return _checkcoupon


def checkaccount(i):
    instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
    sum, = web.ctx.orm.query(func.sum(orm.Ticket.regular)).filter_by(tag_id=instance.onsale.id).filter(orm.Ticket.id.in_(map(int, i.selected.split(",")))).first()
    for coupon in i.coupon.split(",") if i.coupon else []:
        coupon_id, code = coupon.split("-")
        coupon_id = int(coupon_id)
        amount, = web.ctx.orm.query(orm.Coupon.amount).filter_by(tag_id=instance.onsale.id).filter_by(id=coupon_id).filter_by(code=code).filter_by(sold_id=None).first()
        sum -= amount
    if web.input().has_key("with_shipment"):
        sum += 1
    if sum <= 0:
        return True
    if i.payment not in ['banktransfer', 'debit']:
        return False
    if i.payment == 'debit':
        if not i.account_holder:
            return False
        if not iban.ibanvalid(i.account_iban):
            return False
        if len(i.account_bic.strip()) not in [8, 11] or i.account_bic.strip()[4:6].upper() != i.account_iban.strip()[:2].upper():
            return False
    return True

def checkshipment(i):
    if web.input().has_key("with_shipment"):
        if not i.shipment_firstname or not i.shipment_surname or not i.shipment_street or not i.shipment_zip or not i.shipment_city:
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
                         web.form.Textbox("street", description="Straße", size=50),
                         web.form.Textbox("zip", description="PLZ"),
                         web.form.Textbox("city", description="Ort", size=50),
                         web.form.Textbox("lateral", description="Position lateral (siehe Karte unten)", readonly="readonly"),
                         web.form.Textbox("longitudinal", description="Position longitudinal (siehe Karte unten)", readonly="readonly"),
                         web.form.Textbox("phone", description="Telefon (mehrere möglich; auch gern Fax-Nr.)", size=50),
                         web.form.Textbox("email", description="E-Mail (mehrere mit Komma getrennt möglich)", size=50),
                         web.form.Checkbox("email_private", description="E-Mail auf der Chorliste verstecken", value="yes"),
                         web.form.Textbox("birthday", description="Geburtstag (freiwillig; Format TT.MM.JJJJ)"),
                         web.form.Checkbox("birthday_private", description="Geburtstag auf der Chorliste verstecken", value="yes"),
                         web.form.Textarea("notes", description="Notizen (nur intern verwendet)", cols=50, rows=5),
                         web.form.Button("submit", type="submit", html=u"Daten ändern"),
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
        form.email_private.checked = self.member.email_private
        form.birthday.value = self.member.birthday and self.member.birthday.strftime("%d.%m.%Y") or ""
        form.birthday_private.checked = self.member.birthday_private
        form.notes.value = self.member.note
        return render.page("/member/data.html", render.member.data(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())

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
            self.member.email_private = web.input().has_key("email_private")
            birthday = get_birthday(form.d)
            if birthday is True:
                self.member.birthday = None
            else:
                self.member.birthday = birthday
            self.member.birthday_private = web.input().has_key("birthday_private")
            self.member.note = form.d.notes
            new = unicode(self.member)
            if old != new:
                web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Änderung von Mitgliederdaten", self.member, self.member))
            raise web.seeother("index.html")
        else:
            return render.page("/member/data.html", render.member.data(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())


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
                           web.form.Button("submit", type="submit", html=u"Zugang einrichten bzw. ändern"),
                           validators = [web.form.Validator("Altes Passwort stimmt nicht.", checkoldpasswd),
                                         web.form.Validator("Benutzername wird bereits von einem anderen Chormitglied verwendet.", checkloginavailable),
                                         web.form.Validator("Passwörter sind nicht identisch.", lambda i: i.newpasswd == i.newpasswd2),
                                         web.form.Validator("Passwort darf nicht leer gelassen werden.", lambda i: i.newpasswd != "")])


class member_access(object):

    @with_member_auth()
    def GET(self):
        form = AccessForm()
        form.login.value = self.member.login
        return render.page("/member/access.html", render.member.access(form), self.member, ticket_sale_open())

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
            return render.page("/member/access.html", render.member.access(form), self.member, ticket_sale_open())


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
        return render.page("/member/message/X/show.html", render.member.message(message, self.member, icons, printview), self.member, ticket_sale_open(), printview=printview)

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
                          .join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance)\
                          .order_by([desc(orm.Tag.instance_order)]).all()
        return render.page("/member/photos.html", render.member.photos(tags), self.member, ticket_sale_open())


class member_photos_album(object):

    @with_member_auth(active_only=True)
    def GET(self, tag):
        photo = web.input().get("photo")
        if photo:
            photo = web.ctx.orm.query(orm.Photo).filter_by(name=photo).join(orm.Tag).filter_by(name=tag).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
            return render.page("/member/photos/X/index.html", render.member.photo(photo), self.member, ticket_sale_open())
        else:
            tag = web.ctx.orm.query(orm.Tag).filter_by(name=tag).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
            page = int(web.input().get("page", "1"))
            return render.page("/member/photos/X/index.html", render.member.album(tag, page), self.member, ticket_sale_open())


class member_photos_labels(object):

    @with_member_auth(active_only=True)
    def GET(self, tag):
        i = web.input()
        photo = web.ctx.orm.query(orm.Photo).filter_by(name=i.photo).join(orm.Tag).filter_by(name=tag).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        if i.action == "save":
            try:
                top = int(i.top)
                left = int(i.left)
                width = int(i.width)
                height = int(i.height)
            except ValueError:
                raise web.BadRequest()
            if top + height < 5:
                height = 5 - top;
            if left + width < 5:
                width = 5 - left;
            if top + height > photo.midheight - 5:
                height = top + height - photo.midheight + 5
                top = photo.midheight - 5
            if left + width > photo.midwidth - 5:
                width = left + width - photo.midwidth + 5
                left = photo.midwidth - 5
            if i.id == "new":
                label = orm.PhotoLabel(photo, top, left, width, height, i.text)
                web.ctx.orm.add(label)
                web.ctx.orm.commit()
            else:
                label = web.ctx.orm.query(orm.PhotoLabel).filter_by(id=int(i.id.split("-")[1])).filter_by(photo=photo).one()
                label.top = top
                label.left = left
                label.width = width
                label.height = height
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
        photo = web.ctx.orm.query(orm.Photo).filter_by(name=name).join(orm.Tag).filter_by(name=tag).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        try:
            type = web.input().get("type")
            if type == "thumb":
                f = open(photo.thumbname)
            elif type == "mid":
                f = open(photo.midname)
            else:
                f = open(photo.filename)
        except:
            raise web.NotFound()
        web.header("Content-Type", "image/jpeg")
        return f

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

class member_admin_nostatus(object):

    @with_member_auth(admin_only=True)
    def GET(self):
        web.header('Content-Type','text/plain')
        return "no content"


# {{{ admin members
class member_admin_members(member_admin_work_on_selection):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("withorwithout", [("with", "mit"), ("without", "ohne")]),
                             web.form.Dropdown("tag", [(tag.id, tag.name) for tag in self.instance.tags]),
                             *[web.form.Checkbox(name="member_%i" % member.id, value="yes") for member in self.instance.members])

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        for member in self.members():
            form["member_%i" % member.id].checked = True
        inaktiv_ids = set(member.id for member in web.ctx.orm.query(orm.Tag).filter_by(name=u"inaktiv").one().members)
        return render.page("/member/admin/members.html", render.member.admin.members(self.instance, form, inaktiv_ids), self.member, ticket_sale_open())

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
            if web.input().get("add") or web.input().get("remove"):
                tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(form.d.tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
                if form.d.withorwithout == "with":
                    members = tag.members
                else:
                    ids = set(member.id for member in tag.members)
                    members = [member for member in self.instance.members if member.id not in ids]
                value = bool(web.input().get("add"))
                for member in members:
                    form["member_%i" % member.id].checked = value
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
        inaktiv_ids = set(member.id for member in web.ctx.orm.query(orm.Tag).filter_by(name=u"inaktiv").one().members)
        return render.page("/member/admin/members.html", render.member.admin.members(self.instance, form, inaktiv_ids), self.member, ticket_sale_open())


def get_tags(i, get_list=False):
    if not get_list and not i.tags.split(): # hackish: test for empty/whitespace string
        return True
    return [web.ctx.orm.query(orm.Tag).filter_by(name=tag).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
            for tag in i.tags.split()]


def get_circulars(i, get_list=False):
    if not get_list:
        if not i.messages.split(): # hackish: test for empty/whitespace string
            return True
        else:
            for message in i.messages.split():
                if message.find(":") != -1 and message.split(":", 1)[1] not in ["snailmail", "online", "phone"]:
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
                             web.form.Textbox("street", description="Straße", size=50),
                             web.form.Textbox("zip", description="PLZ"),
                             web.form.Textbox("city", description="Ort", size=50),
                             web.form.Textbox("lateral", description="Position lateral (siehe Karte unten)", readonly="readonly"),
                             web.form.Textbox("longitudinal", description="Position longitudinal (siehe Karte unten)", readonly="readonly"),
                             web.form.Textbox("phone", description="Telefon (mehrere möglich; auch gern Fax-Nr.)", size=50),
                             web.form.Textbox("email", description="E-Mail (mehrere mit Komma getrennt möglich)", size=50),
                             web.form.Checkbox("email_private", description="E-Mail auf der Chorliste verstecken", value="yes"),
                             web.form.Textbox("birthday", description="Geburtstag (Format TT.MM.JJJJ)"),
                             web.form.Checkbox("birthday_private", description="Geburtstag auf der Chorliste verstecken", value="yes"),
                             web.form.Textarea("notes", description="Notizen (nur intern verwendet)", cols=50, rows=5),
                             web.form.Textbox("tags", description="Tags", size=50),
                             web.form.Textbox("messages", description="Chorbriefe", size=50),
                             web.form.Button("submit", type="submit", html=u"Speichern"),
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
        return render.page("/member/admin/member/new.html", render.member.admin.member.new(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())

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
            data["email_private"] = web.input().has_key("email_private")
            data["birthday_private"] = web.input().has_key("birthday_private")
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
            return render.page("/member/admin/member/new.html", render.member.admin.member.new(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())


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
        form.email_private.checked = member.email_private
        form.birthday.value = member.birthday and member.birthday.strftime("%d.%m.%Y") or ""
        form.birthday_private.checked = member.birthday_private
        form.notes.value = member.note
        form.tags.value = " ".join(tag.name for tag in member.tags)
        form.messages.value = " ".join(message.access_by and "%s:%s" % (circular.name, message.access_by) or circular.name
                                       for message, circular in web.ctx.orm.query(orm.Message, orm.Circular).filter_by(member=member).join(orm.Circular).join(orm.Instance).filter_by(name=cfg.instance))
        return render.page("/member/admin/member/X/edit.html", render.member.admin.member.edit(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())

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
            member.email_private = web.input().has_key("email_private")
            birthday = get_birthday(form.d)
            if birthday is True:
                member.birthday = None
            else:
                member.birthday = birthday
            member.birthday_private = web.input().has_key("birthday_private")
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
            return render.page("/member/admin/member/X/edit.html", render.member.admin.member.edit(form, cfg.maps_key[web.ctx.protocol]), self.member, ticket_sale_open())


class member_admin_member_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/member/X/delete.html", render.member.admin.member.delete(member), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        for change in member.changes:
            web.ctx.orm.delete(change)
        for edit in member.edits:
            web.ctx.orm.delete(edit)
        for link in member.links:
            web.ctx.orm.delete(link)
        for message in member.messages:
            web.ctx.orm.delete(message)
        web.ctx.orm.delete(member)
        raise web.seeother("../../members.html")


class member_admin_member_clearpasswd(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/member/X/clearpasswd.html", render.member.admin.member.clearpasswd(member), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, id):
        member = web.ctx.orm.query(orm.Member).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        old = unicode(member)
        member.login = member.salt = member.passwd = None
        new = unicode(member)
        if old != new:
            web.ctx.orm.add(orm.Change(u"%s\n\nwurde geändert in\n\n%s" % (old, new), u"Passwort gelöscht von Mitglied", member, self.member))
        raise web.seeother("../../members.html")


class member_admin_member_changes(object):

    @with_member_auth(admin_only=True)
    def GET(self, member_id=None):
        query = web.ctx.orm.query(orm.Change).join(orm.Member.changes).join(orm.Instance).filter_by(name=cfg.instance).reset_joinpoint()
        if member_id:
            member = web.ctx.orm.query(orm.Member).filter_by(id=int(member_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
            query = query.filter_by(member_id=int(member_id))
        else:
            member = None
        changes = query.order_by([desc(orm.Change.timestamp)])
        return render.page("/member/admin/member/X/changes.html", render.member.admin.member.changes(changes, member), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, member_id=None):
        query = web.ctx.orm.query(orm.Change).join(orm.Member.changes).join(orm.Instance).filter_by(name=cfg.instance).reset_joinpoint()
        if member_id:
            query = query.filter_by(member_id=int(member_id))
        change = query.filter_by(id=int(web.input().id)).one()
        web.ctx.orm.delete(change)
        raise web.seeother("changes.html")
# }}} admin members

# {{{ admin print
PrintForm = web.form.Form(web.form.Dropdown("format", [(format.name, format.description)
                                                       for format in cfg.formats], description="Format"),
                          web.form.Textbox("description", description="ggf. Beschreibung"),
                          web.form.Hidden("selection"),
                          web.form.Button("submit", type="submit", html=u"Erzeugen"))

class member_admin_print(member_admin_work_on_selection):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = PrintForm()
        members = self.members()
        form.selection.value = ",".join([str(member.id) for member in members])
        return render.page("/member/admin/print.html", render.member.admin._print(form, members), self.member, ticket_sale_open())

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
            if format.processor == "xml":
                filename = os.path.join(cfg.tmppath, "%s.xml" % cfg.instance)
                f = open(filename, "w")
                x = xml.sax.saxutils.XMLGenerator(f, "utf-8")
                x.startDocument()
                x.startElement("members", {"info": form.d.description})
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
                            if format.hide_private and name == "email" and member.email_private:
                                value = ""
                            if format.hide_private and name == "birthday" and member.birthday_private:
                                value = ""
                            x.startElement(name, {})
                            x.characters("\n%s\n" % value)
                            x.endElement(name)
                            x.characters("\n")
                        x.startElement("tags", {})
                        x.characters("\n")
                        for tag in member.tags:
                            x.startElement("tag", {})
                            x.characters("\n%s\n" % tag.name)
                            x.endElement("tag")
                            x.characters("\n")
                        x.endElement("tags")
                        x.characters("\n")
                        x.endElement("member")
                        x.characters("\n")
                    x.endElement("memberGroup")
                    x.characters("\n")
                x.endElement("members")
                x.characters("\n")
                f.close()
                os.system("%s %s %s > %s.result 2> %s.err" % (cfg.xsltproc, os.path.join(path, "formats", format.xslt), filename, filename[:-4], filename[:-4]))
                web.header("Content-Type", format.mime)
                if format.extension:
                    web.header("Content-Disposition", "attachment; filename=\"%s.%s\"" % (cfg.instance, format.extension))
                f = open(os.path.join(cfg.tmppath, "%s.result" % cfg.instance), "rb")
                data = f.read()
                f.close()
                return data
            else:
                filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
                f = codecs.open(filename, "w", encoding="utf-8")
                f.write(u"\\documentclass{%s}\n" % format.cls.split(".")[0])
                f.write(u"\\usepackage[utf8]{inputenc}\n")
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
                            if format.hide_private and name == "email" and member.email_private:
                                value = ""
                            if format.hide_private and name == "birthday" and member.birthday_private:
                                value = ""
                            f.write(u"\\member%s{%s}%%\n" % (name.capitalize(), TeX_escape(value)))
                        f.write(u"\\memberTags{%s}%%\n" % ", ".join(tag.name for tag in member.tags))
                        f.write(u"\\end{member}%\n")
                    f.write(u"\\end{memberGroup}%\n")
                f.write(u"\\end{members}%\n")
                f.write(u"\\end{document}\n")
                f.close()
                shutil.copy(os.path.join(path, "formats", format.cls), cfg.tmppath)
                if hasattr(format, 'files'):
                    for file in format.files:
                        shutil.copy(os.path.join(path, "formats", file), cfg.tmppath)
                try:
                    os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
                except OSError:
                    pass
                try:
                    os.unlink(os.path.join(cfg.tmppath, "%s.aux" % cfg.instance))
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
            return render.page("/member/admin/print.html", render.member.admin._print(form, members), self.member, ticket_sale_open())
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
        tickets = web.ctx.orm.query(orm.Ticket.tag_id, func.count().label("count")).group_by(orm.Ticket.tag_id).filter(or_(orm.Ticket.sold_id != None, orm.Ticket.wheelchair != 'only')).subquery()
        tags = web.ctx.orm.query(orm.Tag, all.c.count, all.c.ids, selected.c.count, selected.c.ids, photos.c.count, tickets.c.count)\
                          .outerjoin((all, orm.Tag.id == all.c.tag_id))\
                          .outerjoin((selected, orm.Tag.id == selected.c.tag_id))\
                          .outerjoin((photos, orm.Tag.id == photos.c.tag_id))\
                          .outerjoin((tickets, orm.Tag.id == tickets.c.tag_id))\
                          .join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance)\
                          .order_by(orm.Tag.instance_order).all()
        return render.page("/member/admin/tags.html", render.member.admin.tags(tags, members), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self):
        action, = [key for key in web.input().keys() if key != "selection"]
        action, tag = action.split("_")
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
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
                             web.form.Checkbox("visible", description="sichtbar", value="yes"),
                             web.form.Textbox("photopath", description="Foto-Verzeichnis", size=50),
                             web.form.Textbox("photographer", description="Fotograf", size=50),
                             web.form.Textbox("labeledphotos", description="beschriftbare Fotos", size=50),
                             web.form.Textbox("ticket_title", description="Karten-Titel", size=50),
                             web.form.Textbox("ticket_description", description="Karten-Beschreibung", size=50),
                             web.form.Textbox("ticketmap_latexname", description="Karten-Plan (Name der LaTeX class option)", size=50),
                             web.form.Button("submit", type="submit", html=u"Speichern"))


class member_admin_tag_new(member_admin_tag_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        try:
            photopaths = [os.path.normpath(os.path.join(cfg.photopath, dir)) for dir in sorted(os.listdir(cfg.photopath))]
        except OSError:
            photopaths = []
        return render.page("/member/admin/tag/new.html", render.member.admin.tag.new(self.form(), photopaths), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        instance = session.query(orm.Instance).filter_by(name=cfg.instance).one()
        try:
            form = self.form()
            if form.validates():
                web.header("Content-Type", "text/plain; charset=utf-8")
                web.header("Transfer-Encoding", "chunked")
                tag = orm.Tag(form.d.name, form.d.description, web.input().has_key("visible"), form.d.photopath, form.d.photographer, form.d.ticket_title, form.d.ticket_description, form.d.ticketmap_latexname)
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
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        form = self.form(skip_tag=tag)
        form.name.value = tag.name
        form.description.value = tag.description
        form.visible.checked = tag.visible
        form.photopath.value = tag.photopath
        form.photographer.value = tag.photographer
        form.labeledphotos.value = " ".join(photo.name for photo in tag.photos if photo.allow_labels)
        form.ticket_title.value = tag.ticket_title
        form.ticket_description.value = tag.ticket_description
        form.ticketmap_latexname.value = tag.ticketmap_latexname
        form.pos.value = str(self.instance.tags.index(tag))
        try:
            photopaths = [os.path.normpath(os.path.join(cfg.photopath, dir)) for dir in sorted(os.listdir(cfg.photopath))]
        except OSError:
            photopaths = []
        return render.page("/member/admin/tag/X/edit.html", render.member.admin.tag.edit(form, photopaths), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, id):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        instance = session.query(orm.Instance).filter_by(name=cfg.instance).one()
        try:
            tag = session.query(orm.Tag).filter_by(id=int(id)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
            form = self.form(skip_tag=tag)
            if form.validates():
                web.header("Content-Type", "text/plain; charset=utf-8")
                web.header("Transfer-Encoding", "chunked")
                tag.name = form.d.name
                tag.description = form.d.description
                tag.visible = web.input().has_key("visible")
                tag.photopath = form.d.photopath
                tag.photographer = form.d.photographer
                tag.ticket_title = form.d.ticket_title
                tag.ticket_description = form.d.ticket_description
                tag.ticketmap_latexname = form.d.ticketmap_latexname
                instance.tags.remove(tag)
                instance.insert_tag(int(form.d.pos), tag)
                photos = dict((photo.name, photo)
                              for photo in session.query(orm.Photo).join(orm.Tag).filter_by(id=int(id)).join((orm.Instance, orm.Tag.instance_id==orm.Instance.id)).filter_by(name=cfg.instance))
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
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/tag/X/delete.html", render.member.admin.tag.delete(tag), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, id):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(id)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        web.ctx.orm.delete(tag)
        raise web.seeother("../../tags.html")
# }}} admin tags

# {{{ admin tickets
def ticketmap(tag, include_wheelchair_only=False, selected=[], sold=None):
    i = Image.fromstring("RGB", (tag.ticketmap_width, tag.ticketmap_height), tag.ticketmap)
    if not include_wheelchair_only:
        tickets = [ticket for ticket in tag.tickets if ticket.wheelchair != 'only' or ticket.sold_id is not None]
    else:
        tickets = tag.tickets
    for ticket in tickets:
        if ticket.sold_id is None or sold and ticket.sold == sold:
            d = ticket.image_strong
        else:
            d = ticket.image_light
        i2 = Image.fromstring("RGBA", (ticket.right-ticket.left, ticket.bottom-ticket.top), d)
        i.paste(i2, (ticket.left, ticket.top, ticket.right, ticket.bottom), i2)
        if ticket.id in selected:
            draw = ImageDraw.Draw(i)
            x = (ticket.left + ticket.right) / 2
            y = (ticket.top + ticket.bottom) / 2
            draw.ellipse((x-5, y-5, x+5, y+5), fill=(0, 0, 0))
            del draw
    f = cStringIO.StringIO()
    i.save(f, "png")
    f.seek(0)
    return f.getvalue()


MapPrintForm = web.form.Form(web.form.Dropdown("mapformat", [(mapformat.name, mapformat.description)
                                                             for mapformat in cfg.mapformats], description="Format"),
                             web.form.Button("submit", type="submit", html=u"Erzeugen"))

class member_admin_tickets(object):

    def populate(self, tag):
        self.form = MapPrintForm()
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        self.tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        self.total = web.ctx.orm.query(func.count().label("count"),
                                       func.sum(orm.Ticket.regular).label("sum")).filter(orm.Ticket.tag_id==self.tag.id).filter(or_(orm.Ticket.sold_id!=None, orm.Ticket.wheelchair != 'only')).first()
        self.available = web.ctx.orm.query(func.count().label("count"),
                                           func.sum(orm.Ticket.regular).label("sum")).filter(orm.Ticket.tag_id==self.tag.id).filter(orm.Ticket.sold_id==None).filter(orm.Ticket.wheelchair != 'only').first()
        tickets = web.ctx.orm.query(orm.Ticket.sold_id,
                                    func.count().label("count"),
                                    func.sum(orm.Ticket.regular).label("sum")).filter(orm.Ticket.tag_id==self.tag.id).group_by(orm.Ticket.sold_id).subquery()
        coupons = web.ctx.orm.query(orm.Coupon.sold_id,
                                    func.sum(orm.Coupon.amount).label("sum")).filter(orm.Coupon.tag_id==self.tag.id).group_by(orm.Coupon.sold_id).subquery()
        self.booked = web.ctx.orm.query(orm.Sold, tickets.c.count, tickets.c.sum, coupons.c.sum)\
                                 .outerjoin((tickets, orm.Sold.id == tickets.c.sold_id))\
                                 .outerjoin((coupons, orm.Sold.id == coupons.c.sold_id))\
                                 .order_by(orm.Sold.id).filter(orm.Sold.tag_id==self.tag.id).all()
        self.booked_sum = web.ctx.orm.query(func.count().label("count"),
                                            func.sum(orm.Ticket.regular).label("sum")).filter(orm.Ticket.tag_id==self.tag.id).filter(orm.Ticket.sold_id!=None).first()
        self.coupon_used = web.ctx.orm.query(func.sum(orm.Coupon.amount).label("sum")).filter(orm.Coupon.tag_id==self.tag.id).filter(orm.Coupon.sold_id!=None).first()
        self.coupon_available = web.ctx.orm.query(func.sum(orm.Coupon.amount).label("sum")).filter(orm.Coupon.tag_id==self.tag.id).filter(orm.Coupon.sold_id==None).first()


    @with_member_auth(admin_only=True)
    def GET(self, tag):
        self.populate(tag)
        return render.page("/member/admin/tickets/X/index.html", render.member.admin.tickets(self, pickup=web.input().get("pickup")), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        self.populate(tag)
        if web.input().get("action_activate"):
            self.instance.onsale = self.tag
        elif web.input().get("action_deactivate"):
            self.instance.onsale = None
        elif web.input().get("action_open"):
            self.instance.sale_temporarily_closed = False
        elif web.input().get("action_close"):
            self.instance.sale_temporarily_closed = True
        elif web.input().get("action_bank_transfer_enable"):
            self.instance.bank_transfer_possible = True
        elif web.input().get("action_bank_transfer_disable"):
            self.instance.bank_transfer_possible = False
        elif web.input().get("action_shipment_enable"):
            self.instance.shipment_possible = True
        elif web.input().get("action_shipment_disable"):
            self.instance.shipment_possible = False
        elif self.form.validates():
            mapformat, = [mapformat for mapformat in cfg.mapformats if mapformat.name == self.form.d.mapformat]

            def safeint(x):
                try:
                    return 0, int(x)
                except ValueError:
                    return 1, x

            tickets = sorted(web.ctx.orm.query(orm.Ticket).filter_by(tag_id=self.tag.id).filter(or_(orm.Ticket.sold_id != None, orm.Ticket.wheelchair != 'only')),
                             key=lambda ticket: (safeint(ticket.block), safeint(ticket.row), safeint(ticket.seat)))
            full_sheets, on_last_page = divmod(len(tickets), mapformat.order)
            sheet = pos = 0
            for ticket in tickets:
                ticket.sheet = sheet
                if sheet == full_sheets or (sheet == full_sheets - 1 and pos >= on_last_page > 0):
                    sheet = 0
                    pos += 1
                else:
                    sheet += 1
            tickets.sort(key=lambda ticket: ticket.sheet)

            try:
                os.makedirs(cfg.tmppath)
            except OSError:
                pass
            if mapformat.processor == "xml":
                filename = os.path.join(cfg.tmppath, "%s.xml" % cfg.instance)
                f = open(filename, "w")
                x = xml.sax.saxutils.XMLGenerator(f, "utf-8")
                x.startDocument()
                x.startElement("tickets", {})
                x.characters("\n")
                for ticket in tickets:
                    x.startElement("ticket", {})
                    x.characters("\n")
                    for name in ["block", "row", "seat", "cathegory", "regular"]:
                        x.startElement(name, {})
                        if name != "row" or ticket.wheelchair != "only":
                            x.characters("\n%s\n" % getattr(ticket, name))
                        x.endElement(name)
                        x.characters("\n")
                    x.endElement("ticket")
                    x.characters("\n")
                x.endElement("tickets")
                x.characters("\n")
                f.close()
                os.system("%s %s %s > %s.result 2> %s.err" % (cfg.xsltproc, os.path.join(path, "formats", mapformat.xslt), filename, filename[:-4], filename[:-4]))
                web.header("Content-Type", mapformat.mime)
                if mapformat.extension:
                    web.header("Content-Disposition", "attachment; filename=\"%s.%s\"" % (cfg.instance, mapformat.extension))
                f = open(os.path.join(cfg.tmppath, "%s.result" % cfg.instance), "rb")
                data = f.read()
                f.close()
                return data
            else:
                filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
                f = codecs.open(filename, "w", encoding="utf-8")
                f.write(u"\\documentclass[%s]{%s}\n" % (self.tag.ticketmap_latexname, mapformat.cls.split(".")[0]))
                f.write(u"\\usepackage[utf8]{inputenc}\n")
                f.write(u"\\begin{document}%\n")
                f.write(u"\\socTitle{%s}{%s}%%\n" % (self.tag.ticket_title, self.tag.ticket_description))
                for ticket in tickets:
                    if ticket.wheelchair == "only":
                        f.write(u"\\socSeat{%s}{}{%s}{%s}{strong}%%\n" % (ticket.block, ticket.seat, ticket.cathegory))
                    else:
                        f.write(u"\\socSeat{%s}{%s}{%s}{%s}{strong}%%\n" % (ticket.block, ticket.row, ticket.seat, ticket.cathegory))
                f.write(u"\\socStat%\n")
                f.write(u"\\end{document}\n")
                f.close()
                shutil.copy(os.path.join(path, "formats", mapformat.cls), cfg.tmppath)
                shutil.copy(os.path.join(path, "formats", "%s.clo" % self.tag.ticketmap_latexname), cfg.tmppath)
                try:
                    os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
                except OSError:
                    pass
                try:
                    os.unlink(os.path.join(cfg.tmppath, "%s.aux" % cfg.instance))
                except OSError:
                    pass
                os.system("cd %s; %s %s > %s.out 2>&1" % (cfg.tmppath, cfg.pdflatex, filename, filename[:-4]))
                f = open(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance), "rb")
                pdf = f.read()
                f.close()
                web.header("Content-Type", "application/pdf")
                web.header("Content-Disposition", "attachment; filename=\"%s.pdf\"" % cfg.instance)
                return pdf
        return render.page("/member/admin/tickets/X/index.html", render.member.admin.tickets(self), self.member, ticket_sale_open())

class member_admin_ticketmappng(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        selected = web.input().get("selected")
        if selected:
            selected = map(int, selected.split(','))
        else:
            selected = []
        sold = web.input().get("sold")
        if sold:
            sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        i = ticketmap(tag, include_wheelchair_only=sold is not None, selected=selected, sold=sold)
        web.header("Content-Type", "image/png")
        web.header("Cache-Control", "no-cache, must-revalidate")
        return i


class member_admin_ticketmappdf(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        booked = web.input().get("booked")
        available = web.input().get("available")
        sold = web.input().get("sold")
        if sold:
            sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        try:
            os.makedirs(cfg.tmppath)
        except OSError:
            pass
        filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
        f = codecs.open(filename, "w", encoding="utf-8")
        f.write(u"\\documentclass[%s]{map}\n" % tag.ticketmap_latexname)
        f.write(u"\\usepackage[utf8]{inputenc}\n")
        f.write(u"\\begin{document}\n")
        f.write(u"\\socTitle{%s}{%s}%%\n" % (tag.ticket_title, tag.ticket_description))
        tickets = []
        for ticket in web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id):
            if sold:
                if ticket in sold.tickets:
                    ticket.lum = "strong"
                elif ticket.wheelchair != 'only' or ticket.sold_id is not None:
                    ticket.lum = "light"
                else:
                    ticket.lum = None
            else:
                if ticket.wheelchair != 'only' or ticket.sold_id is not None:
                    if (available and ticket.sold_id is not None) or (booked and ticket.sold_id is None):
                        ticket.lum = "light"
                    else:
                        ticket.lum = "strong"
                elif ticket.wheelchair != 'only':
                    ticket.lum = "light"
                else:
                    ticket.lum = None
            if ticket.lum:
                tickets.append(ticket)
        tickets.sort(key=lambda ticket: ticket.lum)
        for ticket in tickets:
            f.write(u"\\socSeat{%s}{%s}{%s}{%s}{%s}\n" % (ticket.block, ticket.row, ticket.seat, ticket.cathegory, ticket.lum))
        f.write(u"\\socStat%\n")
        f.write(u"\\end{document}\n")
        f.close()
        shutil.copy(os.path.join(path, "formats", "map.cls"), cfg.tmppath)
        shutil.copy(os.path.join(path, "formats", "%s.clo" % tag.ticketmap_latexname), cfg.tmppath)
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
        except OSError:
            pass
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.aux" % cfg.instance))
        except OSError:
            pass
        os.system("cd %s; %s %s > %s.out 2>&1" % (cfg.tmppath, cfg.pdflatex, filename, filename[:-4]))
        f = open(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance), "rb")
        pdf = f.read()
        f.close()
        web.header("Content-Type", "application/pdf")
        web.header("Content-Disposition", "attachment; filename=\"%s.pdf\"" % cfg.instance)
        return pdf


class SeatLoadHandler(xml.sax.handler.ContentHandler):

    def __init__(self, tag):
        self.tag = tag
        self.tickets = dict(((ticket.block, ticket.row, ticket.seat), ticket)
                            for ticket in web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id))

    def startElement(self, name, attrs):
        if name == "seat":
            attrs = dict((str(key), value) for key, value in attrs.items())
            attrs["image_light"] = attrs["image_light"].decode('hex')
            attrs["image_strong"] = attrs["image_strong"].decode('hex')
            attrs["left"] = int(attrs["left"])
            attrs["top"] = int(attrs["top"])
            attrs["right"] = int(attrs["right"])
            attrs["bottom"] = int(attrs["bottom"])
            try:
                ticket = self.tickets[attrs["block"], attrs["row"], attrs["seat"]]
            except KeyError:
                orm.Ticket(tag=self.tag, **attrs)
            else:
                for key in attrs:
                    setattr(ticket, key, attrs[key])


class member_admin_tickets_map(object):

    def form(self):
        return web.form.Form(web.form.File("background", description="Hintergrund"),
                             web.form.File("seats", description="Sitzplätze-Daten"),
                             web.form.Button("submit", type="submit", html=u"Speichern"))

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        form = self.form()
        return render.page("/member/admin/tickets/X/map.html", render.member.admin.ticket.map(form, tag), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        form = self.form()
        if form.validates():
            if form.d.background:
                f = cStringIO.StringIO()
                f.write(form.d.background)
                f.seek(0)
                i = Image.open(f)
                tag.ticketmap = i.tobytes()
                tag.ticketmap_width, tag.ticketmap_height = i.size
            if form.d.seats:
                xml.sax.parseString(form.d.seats, SeatLoadHandler(tag))
        raise web.seeother("index.html")


class member_admin_tickets_coupon(object):

    def form(self):
        return web.form.Form(web.form.Textbox("count", web.form.Validator('Positive Zahl erwartet.', lambda x: int(x)>0), value="1", description="Anzahl", size=10),
                             web.form.Textbox("amount", web.form.Validator('Positive Zahl erwartet.', lambda x: int(x)>0), description="Wert", size=10),
                             web.form.Button("submit", type="submit", html=u"Erzeugen"),
                             )

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        coupons = web.ctx.orm.query(orm.Coupon).filter_by(tag=tag).order_by(orm.Coupon.id).all()
        form = self.form()
        return render.page("/member/admin/tickets/X/coupon.html", render.member.admin.ticket.coupon(form, tag, coupons), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        coupons = web.ctx.orm.query(orm.Coupon).filter_by(tag=tag).all()
        form = self.form()
        if form.validates():
            for i in range(int(form.d.count)):
                orm.Coupon(amount=int(form.d.amount), tag=tag)
            raise web.seeother("coupon.html")
        return render.page("/member/admin/tickets/X/coupon.html", render.member.admin.ticket.coupon(form, tag, coupons), self.member, ticket_sale_open())


class member_admin_tickets_couponspdf(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        try:
            os.makedirs(cfg.tmppath)
        except OSError:
            pass
        filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
        f = codecs.open(filename, "w", encoding="utf-8")
        f.write(u"\\documentclass[%s]{coupon}\n" % tag.ticketmap_latexname)
        f.write(u"\\usepackage[utf8]{inputenc}\n")
        f.write(u"\\begin{document}%\n")
        for coupon in tag.coupons:
            f.write(u"\\socCoupon{%i-%s}{%i}%%\n" % (coupon.id, coupon.code, coupon.amount))
        f.write(u"\\end{document}\n")
        f.close()
        shutil.copy(os.path.join(path, "formats", "coupon.cls"), cfg.tmppath)
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
        except OSError:
            pass
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.aux" % cfg.instance))
        except OSError:
            pass
        os.system("cd %s; %s %s > %s.out 2>&1" % (cfg.tmppath, cfg.pdflatex, filename, filename[:-4]))
        f = open(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance), "rb")
        pdf = f.read()
        f.close()
        web.header("Content-Type", "application/pdf")
        web.header("Content-Disposition", "attachment; filename=\"%s.pdf\"" % cfg.instance)
        return pdf


class member_admin_tickets_newsletter(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        newsletters = web.ctx.orm.query(orm.Newsletter).join(orm.Instance).filter_by(name=cfg.instance).all()
        return render.page("/member/admin/tickets/X/newsletter.html", render.member.admin.ticket.newsletter(newsletters), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        session = scoped_session(sessionmaker(bind=engine)) # need a local session for chunked response
        tag = session.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        newsletters = session.query(orm.Newsletter).join(orm.Instance).filter_by(name=cfg.instance).all()
        web.header("Content-Type", "text/plain; charset=utf-8")
        web.header("Transfer-Encoding", "chunked")
        yield "sending %i emails…\n" % len(newsletters)
        s = smtplib.SMTP()
        s.connect()
        for i, newsletter in enumerate(newsletters):
            msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.newsletter_text(tag, newsletter)).encode("utf-8"), _charset="utf-8")
            msg["Subject"] = u"Schwäbischer Oratorienchor: Kartenverkauf gestartet"
            msg["From"] = cfg.from_email
            msg["To"] = newsletter.email
            msg["Date"] = email.Utils.formatdate(localtime=True)
            msg["Precedence"] = "bulk"
            yield "%i: %s\n" % (i+1, newsletter.email)
            s.sendmail(cfg.from_email, [newsletter.email], msg.as_string())
        s.close()
        yield "complete.\n"
        session.close()


class member_admin_tickets_clean(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        return render.page("/member/admin/tickets/X/clean.html", render.member.admin.ticket.clean(), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        web.ctx.orm.query(orm.Sold).filter(orm.Sold.tag_id==tag).filter(orm.Sold.online==True).update(dict(account_holder='', account_iban='', account_bic='',
                                                                             name='', email='', shipment_firstname='', shipment_surname='',
                                                                             shipment_street='', shipment_zip='', shipment_city='', gender='female'))
        for coupon in web.ctx.orm.query(orm.Coupon).filter(orm.Coupon.tag_id==tag).filter(orm.Coupon.sold_id==None).all():
            web.ctx.orm.delete(coupon)
        web.ctx.orm.commit()
        raise web.seeother("index.html")


class member_admin_ticket_form(object):

    def form(self, tag, sold=None):
        return web.form.Form(web.form.Dropdown("gender", [("female", "Frau"), ("male", "Herr")], description="Anrede"),
                             web.form.Textbox("name", notnull, description=u"Name", size=50),
                             web.form.Textbox("email", description="E-Mail", size=50),
                             web.form.Textbox("coupon", description="Gutschein", size=50),
                             web.form.Checkbox("online", description="online-Bestellung", value="yes"),
                             web.form.Hidden("selected"),
                             web.form.Button("submit", type="submit", html=u"Speichern"),
                             validators = [web.form.Validator("Formatfehler in E-Mail-Adresse(n).", checkemail),
                                           web.form.Validator("Ungültiger Gutschein.", checkcoupon(tag, sold))])


class member_admin_tickets_new(member_admin_ticket_form):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        form = self.form(tag)
        return render.page("/member/admin/tickets/X/new.html", render.member.admin.ticket.new(form, tag), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        form = self.form(tag)
        x = web.input().get("map.x")
        y = web.input().get("map.y")
        clicked = None
        if x and y:
            x = int(x)
            y = int(y)
            clicked = web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id).filter(orm.Ticket.left<x).filter(orm.Ticket.right>x).filter(orm.Ticket.top<y).filter(orm.Ticket.bottom>y).first()
        if form.validates() and x is None and y is None:
            sold = orm.Sold(gender=form.d.gender, name=form.d.name, email=form.d.email, online=web.input().has_key("online"), tag=tag, payment='banktransfer' if web.input().has_key("online") else '')
            if form.d.selected:
                web.ctx.orm.commit()
                for ticket_id in set(map(int, form.d.selected.split(","))):
                    web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id).filter_by(id=ticket_id).filter_by(sold_id=None).update({"sold_id": sold.id})
            if form.d.coupon:
                web.ctx.orm.commit()
                for coupon in form.d.coupon.split(","):
                    coupon_id, code = coupon.split("-")
                    coupon_id = int(coupon_id)
                    web.ctx.orm.query(orm.Coupon).filter_by(tag_id=tag.id).filter_by(id=coupon_id).filter_by(code=code).filter_by(sold_id=None).update({"sold_id": sold.id})
            raise web.seeother("index.html")
        else:
            if form.d.selected:
                selected = set(map(int, form.d.selected.split(",")))
            else:
                selected = set()
            if clicked:
                if clicked.id in selected:
                    selected.remove(clicked.id)
                else:
                    selected.add(clicked.id)
            form.selected.value = ",".join(map(str, selected))
            return render.page("/member/admin/tickets/X/new.html", render.member.admin.ticket.new(form, tag), self.member, ticket_sale_open())


class member_admin_tickets_edit(member_admin_ticket_form):

    @with_member_auth(admin_only=True)
    def GET(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        form = self.form(tag, sold)
        form.gender.value = sold.gender
        form.name.value = sold.name
        form.email.value = sold.email
        form.coupon.value = ", ".join("%i-%s" % (coupon.id, coupon.code) for coupon in sold.coupons)
        form.online.checked = sold.online
        form.selected.value = ",".join(str(ticket.id) for ticket in sold.tickets)
        return render.page("/member/admin/tickets/X/sold/X/edit.html", render.member.admin.ticket.edit(form, tag, sold), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        form = self.form(tag, sold)
        x = web.input().get("map.x")
        y = web.input().get("map.y")
        clicked = None
        if x and y:
            x = int(x)
            y = int(y)
            clicked = web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id).filter(orm.Ticket.left<x).filter(orm.Ticket.right>x).filter(orm.Ticket.top<y).filter(orm.Ticket.bottom>y).first()
        if form.validates() and x is None and y is None:
            sold.gender = form.d.gender
            sold.name = form.d.name
            sold.email = form.d.email
            sold.online = web.input().has_key("online")
            if form.d.selected:
                selected = set(map(int, form.d.selected.split(",")))
            else:
                selected = []
            for ticket in sold.tickets:
                if ticket.id in selected:
                    selected.remove(ticket.id)
                else:
                    ticket.sold_id = None
            for ticket_id in selected:
                web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id).filter_by(id=ticket_id).filter_by(sold_id=None).update({"sold_id": sold.id})
                web.ctx.orm.commit()
            if form.d.coupon:
                coupons = set(coupon.replace(" ", "") for coupon in form.d.coupon.split(","))
            else:
                coupons = []
            for coupon in sold.coupons:
                if "%i-%s" % (coupon.id, coupon.code) in coupons:
                    coupons.remove("%i-%s" % (coupon.id, coupon.code))
                else:
                    coupon.sold_id = None
            for coupon in coupons:
                coupon_id, code = coupon.split("-")
                coupon_id = int(coupon_id)
                web.ctx.orm.query(orm.Coupon).filter_by(tag_id=tag.id).filter_by(id=coupon_id).filter_by(code=code).filter_by(sold_id=None).update({"sold_id": sold.id})
                web.ctx.orm.commit()
            raise web.seeother("../../index.html")
        else:
            if form.d.selected:
                selected = set(map(int, form.d.selected.split(",")))
            else:
                selected = set()
            if clicked:
                if clicked.id in selected:
                    selected.remove(clicked.id)
                else:
                    selected.add(clicked.id)
            form.selected.value = ",".join(map(str, selected))
            return render.page("/member/admin/tickets/X/sold/X/edit.html", render.member.admin.ticket.edit(form, tag, sold), self.member, ticket_sale_open())


class member_admin_tickets_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        return render.page("/member/admin/link/X/sold/X/delete.html", render.member.admin.ticket.delete(sold), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        web.ctx.orm.query(orm.Ticket).filter_by(tag_id=tag.id).filter_by(sold_id=sold.id).update({"sold_id": None})
        web.ctx.orm.delete(sold)
        raise web.seeother("../../index.html")


class member_admin_tickets_pickup(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag, solds):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        filename = os.path.join(cfg.tmppath, "%s.tex" % cfg.instance)
        f = codecs.open(filename, "w", encoding="utf-8")
        f.write(u"\\documentclass{pickup}\n")
        f.write(u"\\usepackage[utf8]{inputenc}\n")
        f.write(u"\\begin{document}\n")
        for sold in solds.split(','):
            sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
            sum = 0
            for ticket in sold.tickets:
                sum += ticket.regular
            if sold.shipment:
                f.write(u"\\socShipment{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}\n" % (sold.gender, sold.name, tag.ticket_title, tag.ticket_description, sold.shipment_firstname, sold.shipment_surname, sold.shipment_street, sold.shipment_zip, sold.shipment_city))
            else:
                f.write(u"\\socPickup{%s}{%s}{%s-%s}{%s-%s}{%s}{%s}{%s}{%s}\n" % (sold.gender, sold.name, sold.id, sold.bankcode, sold.id, sold.pickupcode, "payed" if sold.payed else "not payed", tag.ticket_title, tag.ticket_description, sum))
            for ticket in sold.tickets:
                f.write(u"\\socTicket{%s}{%s}{%s}{%s}{%s}\n" % (ticket.block, ticket.row, ticket.seat, ticket.cathegory, ticket.regular))
            f.write(u"\\clearpage\n")
        f.write(u"\\end{document}\n")
        f.close()
        shutil.copy(os.path.join(path, "formats", "pickup.cls"), cfg.tmppath)
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance))
        except OSError:
            pass
        try:
            os.unlink(os.path.join(cfg.tmppath, "%s.aux" % cfg.instance))
        except OSError:
            pass
        os.system("cd %s; %s %s > %s.out 2>&1" % (cfg.tmppath, cfg.pdflatex, filename, filename[:-4]))
        f = open(os.path.join(cfg.tmppath, "%s.pdf" % cfg.instance), "rb")
        pdf = f.read()
        f.close()
        web.header("Content-Type", "application/pdf")
        web.header("Content-Disposition", "attachment; filename=\"%s.pdf\"" % cfg.instance)
        return pdf


class member_admin_tickets_pay(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        sum = 0
        for ticket in sold.tickets:
            sum += ticket.regular
        for coupon in sold.coupons:
            sum -= coupon.amount
        if sold.shipment:
            sum += 1
        if sold.shipment:
            return render.page("/member/admin/link/X/sold/X/pay.html", render.member.admin.ticket.pay_shipment(sold, sum), self.member, ticket_sale_open())
        return render.page("/member/admin/link/X/sold/X/pay.html", render.member.admin.ticket.pay(sold, sum), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        sold.payed = datetime.datetime.now()
        web.ctx.orm.commit()
        s = smtplib.SMTP()
        s.connect()
        if sold.shipment:
            msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_payed_shipment(tag, sold)).encode("utf-8"), _charset="utf-8")
        else:
            msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_payed(tag, sold)).encode("utf-8"), _charset="utf-8")
        msg["Subject"] = u"Abholkennwort für Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
        msg["From"] = cfg.from_email
        to_emails = sold.email.split(",")
        msg["To"] = to_emails[0]
        if len(to_emails) > 1:
            msg["Cc"] = ",".join(to_emails[1:])
        msg["Date"] = email.Utils.formatdate(localtime=True)
        to_emails.append(cfg.from_email)
        s.sendmail(cfg.from_email, to_emails, msg.as_string())
        s.close()
        raise web.seeother("../../index.html?pickup=%d" % sold.id)


class member_admin_tickets_remind(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        sum = 0
        for ticket in sold.tickets:
            sum += ticket.regular
        for coupon in sold.coupons:
            sum -= coupon.amount
        return render.page("/member/admin/link/X/sold/X/remind.html", render.member.admin.ticket.remind(sold, sum), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag, sold):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        sold = web.ctx.orm.query(orm.Sold).filter_by(id=int(sold)).filter_by(tag_id=tag.id).one()
        web.ctx.orm.commit()
        s = smtplib.SMTP()
        s.connect()
        if sold.shipment:
            msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_remind_shipment(tag, sold)).encode("utf-8"), _charset="utf-8")
        else:
            msg = email.MIMEText.MIMEText(unicode(render.member.admin.ticket.tickets_remind(tag, sold)).encode("utf-8"), _charset="utf-8")
        msg["Subject"] = u"BITTE LESEN: Erinnerung an Ihre Kartenbestellung für den Schwäbischen Oratorienchor"
        msg["From"] = cfg.from_email
        to_emails = sold.email.split(",")
        msg["To"] = to_emails[0]
        if len(to_emails) > 1:
            msg["Cc"] = ",".join(to_emails[1:])
        msg["Date"] = email.Utils.formatdate(localtime=True)
        to_emails.append(cfg.from_email)
        s.sendmail(cfg.from_email, to_emails, msg.as_string())
        s.close()
        raise web.seeother("../../index.html")


class member_admin_tickets_debit(object):

    @with_member_auth(admin_only=True)
    def GET(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        debits = web.ctx.orm.query(orm.Sold).filter_by(tag_id=tag.id).filter_by(payment='debit').order_by(orm.Sold.id).all()
        return render.page("/member/admin/tickets/X/debit.html", render.member.admin.ticket.debit(debits), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, tag):
        tag = web.ctx.orm.query(orm.Tag).filter_by(id=int(tag)).join((orm.Instance, orm.Tag.instance)).filter_by(name=cfg.instance).one()
        debits = web.ctx.orm.query(orm.Sold).filter_by(tag_id=tag.id).filter_by(payment='debit').filter(orm.Sold.id.in_(web.input(selection=[]).get("selection"))).all()
        if web.input().get("make_pickup") is not None:
            raise web.seeother("sold/%s/pickup.html" % ','.join(map(str, [sold.id for sold in debits])))
        if web.input().get("make_debit") is not None:
            debits = list(debits)
            filename = os.path.join(cfg.tmppath, "%s.xml" % cfg.instance)
            f = open(filename, "w")
            x = xml.sax.saxutils.XMLGenerator(f, "utf-8")
            x.startDocument()
            x.startElement("debits", {})
            x.characters("\n")
            total = 0
            for debit in debits:
                x.startElement("debit", {})
                x.characters("\n")
                for name in ["id", "bankcode", "account_holder", "account_iban", "account_bic"]:
                    x.startElement(name, {})
                    x.characters("%s" % debit.__dict__[name])
                    x.endElement(name)
                    x.characters("\n")
                x.startElement("amount", {})
                amount = sum(ticket.regular for ticket in debit.tickets) - sum(coupon.amount for coupon in debit.coupons)
                if debit.shipment:
                    amount += 1
                x.characters("%d" % amount)
                total += amount
                x.endElement("amount")
                x.characters("\n")
                x.startElement("date", {})
                x.characters("%s" % debit.created.strftime('%Y-%m-%d'))
                x.endElement("date")
                x.characters("\n")
                x.endElement("debit")
                x.characters("\n")
            x.startElement("count", {})
            x.characters("%d" % len(debits))
            x.endElement("count")
            x.characters("\n")
            x.startElement("total", {})
            x.characters("%d" % total)
            x.endElement("total")
            x.characters("\n")
            x.startElement("now", {})
            x.characters(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
            x.endElement("now")
            x.characters("\n")
            x.startElement("now_plus_ten", {})
            x.characters((datetime.datetime.now()+datetime.timedelta(10)).strftime('%Y-%m-%d'))
            x.endElement("now_plus_ten")
            x.characters("\n")
            x.endElement("debits")
            x.characters("\n")
            f.close()
            os.system("%s %s %s > %s.result 2> %s.err" % (cfg.xsltproc, os.path.join(path, "formats", "sepa.xslt"), filename, filename[:-4], filename[:-4]))
            web.header("Content-Type", "text/xml")
            web.header("Content-Disposition", "attachment; filename=\"%s.xml\"" % cfg.instance)
            f = open(os.path.join(cfg.tmppath, "%s.result" % cfg.instance), "rb")
            data = f.read()
            f.close()
            return data
        else:
            assert web.input().get("book_debit") is not None
            for debit in debits:
                debit.payed = datetime.datetime.now()
            debits = web.ctx.orm.query(orm.Sold).filter_by(tag_id=tag.id).filter_by(payment='debit').all()
            return render.page("/member/admin/tickets/X/debit.html", render.member.admin.ticket.debit(debits), self.member, ticket_sale_open())

# }}} admin tickets

# {{{ admin circulars
class member_admin_circulars(member_admin_work_on_selection):

    def form(self):
        self.instance = web.ctx.orm.query(orm.Instance).filter_by(name=cfg.instance).one()
        return web.form.Form(web.form.Dropdown("circular", [(circular.id, circular.title) for circular in self.instance.circulars], description="Chorbrief"),
                             web.form.Dropdown("action", [("new:none", "neu einstellen und als ungelesen markieren"),
                                                          ("new:online", "neu einstellen und als online gelesen markieren"),
                                                          ("new:phone", "neu einstellen und als per Telefon informiert markieren"),
                                                          ("new:snailmail", "neu einstellen und als Brief gelesen marieren"),
                                                          ("change:none", "als ungelesen markieren"),
                                                          ("change:online", "als online gelesen markieren"),
                                                          ("change:phone", "als per Telefon informiert markieren"),
                                                          ("change:snailmail", "als Brief gelesen marieren"),
                                                          ("delete", "entfernen")], description="Aktion"),
                             web.form.Hidden("selection"),
                             web.form.Button("submit", type="submit", html=u"Ausführen"))

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
        phone = count_ids_stmt.filter_by(access_by=u'phone').subquery()
        phone_selected = count_ids_stmt.filter_by(access_by=u'phone').filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        snailmail = count_ids_stmt.filter_by(access_by=u'snailmail').subquery()
        snailmail_selected = count_ids_stmt.filter_by(access_by=u'snailmail').filter(orm.Message.member_id == func.any([member.id for member in members])).subquery()
        circulars = web.ctx.orm.query(orm.Circular,
                                      total.c.count, total.c.ids,
                                      total_selected.c.count, total_selected.c.ids,
                                      unread.c.count, unread.c.ids,
                                      unread_selected.c.count, unread_selected.c.ids,
                                      online.c.count, online.c.ids,
                                      online_selected.c.count, online_selected.c.ids,
                                      phone.c.count, phone.c.ids,
                                      phone_selected.c.count, phone_selected.c.ids,
                                      snailmail.c.count, snailmail.c.ids,
                                      snailmail_selected.c.count, snailmail_selected.c.ids)\
                               .outerjoin((total, orm.Circular.id == total.c.circular_id))\
                               .outerjoin((total_selected, orm.Circular.id == total_selected.c.circular_id))\
                               .outerjoin((unread, orm.Circular.id == unread.c.circular_id))\
                               .outerjoin((unread_selected, orm.Circular.id == unread_selected.c.circular_id))\
                               .outerjoin((online, orm.Circular.id == online.c.circular_id))\
                               .outerjoin((online_selected, orm.Circular.id == online_selected.c.circular_id))\
                               .outerjoin((phone, orm.Circular.id == phone.c.circular_id))\
                               .outerjoin((phone_selected, orm.Circular.id == phone_selected.c.circular_id))\
                               .outerjoin((snailmail, orm.Circular.id == snailmail.c.circular_id))\
                               .outerjoin((snailmail_selected, orm.Circular.id == snailmail_selected.c.circular_id))\
                               .order_by(orm.Circular.instance_order).all()
        form = self.form()
        form.selection.value = ",".join([str(member.id) for member in members])
        return render.page("/member/admin/circulars.html", render.member.admin.circulars(form, circulars, members), self.member, ticket_sale_open())

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
                             web.form.Button("submit", type="submit", html=u"Ausführen"))

    @with_member_auth(admin_only=True)
    def GET(self):
        return render.page("/member/admin/circular/copy.html", render.member.admin.circular.copy(self.form()), self.member, ticket_sale_open())


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
                             web.form.Button("submit", type="submit", html=u"Speichern"))


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
        return render.page("/member/admin/circular/new.html", render.member.admin.circular.new(form), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            circular = orm.Circular(form.d.name, form.d.title, form.d.html, form.d.email)
            self.instance.insert_circular(int(form.d.pos), circular)
            raise web.seeother("../circulars.html")
        else:
            return render.page("/member/admin/circular/new.html", render.member.admin.circular.new(form), self.member, ticket_sale_open())


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
        return render.page("/member/admin/circular/X/edit.html", render.member.admin.circular.edit(form), self.member, ticket_sale_open())

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
            return render.page("/member/admin/circular/X/edit.html", render.member.admin.circular.edit(form), self.member, ticket_sale_open())


class member_admin_circular_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/circular/X/delete.html", render.member.admin.circular.delete(circular), self.member, ticket_sale_open())

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
        return render.page("/member/admin/circular/X/attachments.html", render.member.admin.circular.attachments(circular), self.member, ticket_sale_open())


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
                             web.form.Button("submit", type="submit", html=u"Speichern"))


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
        return render.page("/member/admin/circular/X/attachment/new.html", render.member.admin.circular.attachment.new(form, self.circular), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self, circular_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form()
        if form.validates():
            attachment = orm.Attachment(form.d.name, form.d.mimetype, form.d.data)
            self.circular.insert_attachment(int(form.d.pos), attachment)
            raise web.seeother("../attachments.html")
        else:
            return render.page("/member/admin/circular/X/attachment/new.html", render.member.admin.circular.attachment.new(form, self.circular), self.member, ticket_sale_open())


class member_admin_attachment_edit(member_admin_attachment_form):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id, attachment_id):
        self.circular = web.ctx.orm.query(orm.Circular).filter_by(id=int(circular_id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_attachment=attachment)
        form.name.value = attachment.name
        form.mimetype.value = attachment.mimetype
        form.pos.value = str(self.circular.attachments.index(attachment))
        return render.page("/member/admin/circular/X/attachment/X/edit.html", render.member.admin.circular.attachment.edit(form, attachment), self.member, ticket_sale_open())

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
            return render.page("/member/admin/circular/X/attachment/X/edit.html", render.member.admin.circular.attachment.edit(form, attachment), self.member, ticket_sale_open())


class member_admin_attachment_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, circular_id, attachment_id):
        attachment = web.ctx.orm.query(orm.Attachment).filter_by(id=int(attachment_id)).join(orm.Circular).filter_by(id=circular_id).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/circular/X/attachment/X/delete.html", render.member.admin.circular.attachment.delete(attachment), self.member, ticket_sale_open())

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
        return render.page("/member/admin/links.html", render.member.admin.links(entrances, members), self.member, ticket_sale_open())

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
                             web.form.Button("submit", type="submit", html=u"Speichern"),
                             validators = [web.form.Validator("Ungültiges Ablaufdatum.", get_expire)])


class member_admin_link_new(member_admin_link_form):

    @with_member_auth(admin_only=True)
    def GET(self):
        form = self.form()
        entrance = web.ctx.orm.query(orm.Entrance).join(orm.Instance).filter_by(name=cfg.instance).order_by([desc(orm.Entrance.expire)]).limit(1).all()
        if entrance:
            form.expire.value = entrance[0].expire.strftime("%d.%m.%Y")
        return render.page("/member/admin/link/new.html", render.member.admin.link.new(form, self.instance), self.member, ticket_sale_open())

    @with_member_auth(admin_only=True)
    def POST(self):
        form = self.form()
        if form.validates():
            entrance = orm.Entrance(form.d.url, get_expire(form.d))
            self.instance.insert_entrance(int(form.d.pos), entrance)
            raise web.seeother("../links.html")
        else:
            return render.page("/member/admin/link/new.html", render.member.admin.link.new(form, self.instance), self.member, ticket_sale_open())


class member_admin_link_edit(member_admin_link_form):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        form = self.form(skip_entrance=entrance)
        form.url.value = entrance.url
        form.expire.value = entrance.expire.strftime("%d.%m.%Y")
        form.pos.value = str(self.instance.entrances.index(entrance))
        return render.page("/member/admin/link/X/edit.html", render.member.admin.link.edit(form, self.instance), self.member, ticket_sale_open())

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
            return render.page("/member/admin/link/X/edit.html", render.member.admin.link.edit(form, self.instance), self.member, ticket_sale_open())


class member_admin_link_delete(object):

    @with_member_auth(admin_only=True)
    def GET(self, id):
        entrance = web.ctx.orm.query(orm.Entrance).filter_by(id=int(id)).join(orm.Instance).filter_by(name=cfg.instance).one()
        return render.page("/member/admin/link/X/delete.html", render.member.admin.link.delete(entrance), self.member, ticket_sale_open())

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
                             web.form.Button("submit", type="submit", html=u"Versenden"))

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
        return render.page("/member/admin/link/X/email.html", render.member.admin.link.email(form, entrance, members, missing), self.member, ticket_sale_open())

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
                body = circular.email % {"firstname": member.firstname, "lastname": member.lastname, "salutation": member.salutation, "uuid": link.uuid}
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
                msg["Precedence"] = "bulk"
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
        print "socmanager  Copyright (C) 2010-2011  André Wobst"
        app.run()
else:
    inner_application = app.wsgifunc()

    class ReverseProxied(object):
        '''Wrap the application in this middleware and configure the 
        front-end server to add these headers, to let you quietly bind 
        this to a URL other than / and to an HTTP scheme that is 
        different than what is used locally.

        In nginx:
        location /myprefix {
            proxy_pass http://192.168.0.1:5001;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Script-Name /myprefix;
            }

        :param app: the WSGI application
        '''
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
            if script_name:
                environ['SCRIPT_NAME'] = script_name
                path_info = environ['PATH_INFO']
                if path_info.startswith(script_name):
                    environ['PATH_INFO'] = path_info[len(script_name):]

            scheme = environ.get('HTTP_X_SCHEME', '')
            if scheme:
                environ['wsgi.url_scheme'] = scheme
            return self.app(environ, start_response)

    application = ReverseProxied(inner_application)

# vim:fdm=marker
