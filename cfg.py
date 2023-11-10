# -*- encoding: utf-8 -*-

import os
parentpath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from web.utils import Storage
from sqlalchemy import __version__ as sqlalchemy_version

sitepath = None
if sqlalchemy_version.startswith("0.5"):
    db = "postgres:///soc"
else:
    db = "postgresql:///soc"
init = "socmembers.xml"
instance = u"soc"
secret = u"..."
cookie = "soclogin"
pdflatex = "/usr/bin/pdflatex"
xsltproc = "/usr/bin/xsltproc"
htpasswd = "/usr/bin/htpasswd"
tmppath = "/tmp/socmanager"
photopath = os.path.join(parentpath, "photos")
thumbpath = os.path.join(parentpath, "var", "spool", "socmanager", "thumb")
midpath = os.path.join(parentpath, "var", "spool", "socmanager", "mid")
recordingpath = os.path.join(parentpath, "cds")
formats = [Storage(processor="tex", name="full", description=u"Komplettliste mit allen Informationen (pdf)", cls="full.cls", merge=None, hide_private=False),
           Storage(processor="tex", name="project", description=u"Projektliste zum Verteilen (pdf)", cls="project.cls", merge=None, hide_private=True),
           Storage(processor="tex", name="chorverband", description=u"Mitgliederliste für Chorverband (pdf)", cls="chorverband.cls", merge=None, hide_private=False),
           Storage(processor="tex", name="address_sticker", description=u"Addressettikten (pdf)", cls="address_sticker.cls", merge="address", hide_private=True),
           Storage(processor="tex", name="address_panel", description=u"Addressaufdruck für Fensterumschläge (pdf)", cls="address_panel.cls", merge="address", hide_private=True),
           Storage(processor="tex", name="badge", description=u"Namensschilder (pdf)", cls="badge.cls", merge=None, hide_private=True, files=["soclogo.pdf"]),
           Storage(processor="tex", name="voucher", description=u"Gutschein (pdf)", cls="voucher.cls", merge=None, hide_private=True),
           Storage(processor="xml", name="kml", description=u"Google Earth Datei (kml)", xslt="kml.xslt", merge="address", mime="application/vnd.google-earth.kml+xml", extension="kml", hide_private=True),
           Storage(processor="xml", name="birthyear", description=u"Anzahl Geburtsjahr in Bereich lt. Beschreibung (txt)", xslt="birthyear.xslt", merge=None, mime="text/plain; charset=utf-8", extension=None, hide_private=False),
           Storage(processor="xml", name="program", description=u"Namensliste für Programmheft (txt)", xslt="program.xslt", merge=None, mime="text/plain; charset=utf-8", extension=None, hide_private=True),
           Storage(processor="xml", name="chorliste", description=u"tabellarische Chorliste (txt)", xslt="chorliste.xslt", merge=None, mime="text/plain; charset=utf-8", extension=None, hide_private=True),
           Storage(processor="xml", name="order", description=u"Adressliste für Notenbestellung (txt)", xslt="order.xslt", merge="address", mime="text/plain; charset=utf-8", extension=None, hide_private=False)]
from_email = "info@schwaebischer-oratorienchor.de"
attachments = [Storage(type="PDF Dokument", mime="application/pdf", icon="pdf.png"),
               Storage(type="Google Earth KML Datei", mime="application/vnd.google-earth.kml+xml", icon="kml.png"),
               Storage(type="iCalendar Datei", mime="text/calendar", icon="ics.png"),
               Storage(type="JPEG Bild", mime="image/jpeg", icon="jpg.png"),
               Storage(type="PNG Bild", mime="image/png", icon="png.png")]
mid_size = 750
thumb_size = 150
mapformats = [Storage(processor="tex", name="map", description=u"Sitzplan (pdf)", cls="map.cls", order=1),
              Storage(processor="tex", name="sepatator", description=u"Trennblätter für Kartenverkauf (pdf)", cls="separator.cls", order=1),
              Storage(processor="tex", name="seats1", description=u"Platzschilder fortlaufend (pdf)", cls="seat.cls", order=1),
              Storage(processor="tex", name="seats24", description=u"Platzschilder hintereinander (pdf)", cls="seat.cls", order=24),
              Storage(processor="tex", name="rows", description=u"Reihenschilder (pdf)", cls="row.cls", order=1),
              Storage(processor="xml", name="tickets1", description=u"Karten-Seriendatei fortlaufend (tex)", xslt="series.xslt", mime="text/plain", extension="tex", order=1),
              Storage(processor="xml", name="tickets6", description=u"Karten-Seriendatei 6 hintereinander (tex)", xslt="series.xslt", mime="text/plain", extension="tex", order=6)]

subscription_initial = 50
subscription_annual = 20
recording = 10
subscription_passwdfile = "/home/wobsta/soc/webdav-passwd"

try:
    from secrets import *
    dev = False
except ImportError:
    print "No secrets found (ok for dev mode; not appropriate for production)."
    dev = True
