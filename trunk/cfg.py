# -*- encoding: utf-8 -*-

from web.utils import Storage

db = "postgres:///soc"
init = "socmembers.xml"
instance = u"soc"
secret = u"..."
cookie = "soclogin"
maps_key = {"http": "...",
            "https": "..."}
pdflatex = "/usr/local/bin/safepdflatex"
xsltproc = "/usr/bin/xsltproc"
tmpdir = "/chroot-texlive2009/work/soc"
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
    from secrets import secret, maps_key
except ImportError:
    print "No secrets found. Adjust configuration."
