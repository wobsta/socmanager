# -*- encoding: utf-8 -*-

from web.utils import Storage
from sqlalchemy import __version__ as sqlalchemy_version

if sqlalchemy_version.startswith("0.5"):
    db = "postgres:///soc"
else:
    db = "postgresql:///soc"
init = "socmembers.xml"
instance = u"soc"
secret = u"..."
cookie = "soclogin"
maps_key = Storage(http="ABQIAAAAnfs7bKE82qgb3Zc2YyS-oBT2yXp_ZAY8_ufC3CFXhHIE1NvwkxSySz_REpPq-4WZA27OwgbtyR3VcA")
pdflatex = "/usr/bin/pdflatex"
xsltproc = "/usr/bin/xsltproc"
tmpdir = "/tmp/socmanager"
formatdir = "formats"
formats = [Storage(type="tex", name="full", description=u"Komplettliste mit allen Informationen (pdf)", cls="full.cls", merge=None),
           Storage(type="tex", name="project", description=u"Projektliste zum Verteilen (pdf)", cls="project.cls", merge=None),
           Storage(type="tex", name="address_sticker", description=u"Addressettikten (pdf)", cls="address_sticker.cls", merge="address"),
           Storage(type="tex", name="address_panel", description=u"Addressaufdruck für Fensterumschläge (pdf)", cls="address_panel.cls", merge="address"),
           Storage(type="tex", name="badge", description=u"Namensschilder (pdf)", cls="badge.cls", merge=None),
           Storage(type="tex", name="voucher", description=u"Gutschein (pdf)", cls="voucher.cls", merge=None),
           Storage(type="xml", name="kml", description=u"Google Earth Datei (kml)", xslt="kml.xslt", merge="address")]
from_email = "info@schwaebischer-oratorienchor.de"
attachments = [Storage(type="PDF Dokument", mime="application/pdf", icon="pdf.png"),
               Storage(type="Google Earth KML Datei", mime="application/vnd.google-earth.kml+xml", icon="kml.png"),
               Storage(type="JPEG Bild", mime="image/jpeg", icon="jpg.png"),
               Storage(type="PNG Bild", mime="image/png", icon="png.png")]
mid_size = 750
thumb_size = 150

try:
    from secrets import *
except ImportError:
    print "No secrets found, running at the default config."
