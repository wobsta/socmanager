<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <kml xmlns="http://earth.google.com/kml/2.2">
      <Document>
        <xsl:for-each select="members/memberGroup">
          <Placemark>
            <name>
              <xsl:for-each select="member">
                <xsl:value-of select="normalize-space(firstname)"/><xsl:text> </xsl:text>
                <xsl:value-of select="normalize-space(lastname)"/>
                <xsl:if test="not(position() = last())"><xsl:text>, </xsl:text></xsl:if>
              </xsl:for-each>
            </name>
            <description>
              <xsl:value-of select="normalize-space(member/street)"/><xsl:text>, </xsl:text>
              <xsl:value-of select="normalize-space(member/zip)"/><xsl:text> </xsl:text>
              <xsl:value-of select="normalize-space(member/city)"/>
            </description>
            <Point>
              <coordinates><xsl:value-of select="normalize-space(member/longitudinal)"/><xsl:text>,</xsl:text><xsl:value-of select="normalize-space(member/lateral)"/><xsl:text>,0</xsl:text></coordinates>
            </Point>
          </Placemark>
        </xsl:for-each>
      </Document>
    </kml>
  </xsl:template>
</xsl:stylesheet>
