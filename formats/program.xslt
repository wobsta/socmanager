<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" />
    <xsl:template match="/">Sopran: <xsl:for-each select="members/memberGroup/member[contains(tags/tag/text(), 'Sopran')]">
        <xsl:value-of select="normalize-space(firstname)"/><xsl:text>~</xsl:text>
        <xsl:value-of select="normalize-space(lastname)"/>
        <xsl:if test="not(position() = last())"><xsl:text>, </xsl:text></xsl:if>
      </xsl:for-each>
Alt: <xsl:for-each select="members/memberGroup/member[contains(tags/tag/text(), 'Alt')]">
        <xsl:value-of select="normalize-space(firstname)"/><xsl:text>~</xsl:text>
        <xsl:value-of select="normalize-space(lastname)"/>
        <xsl:if test="not(position() = last())"><xsl:text>, </xsl:text></xsl:if>
      </xsl:for-each>
Tenor: <xsl:for-each select="members/memberGroup/member[contains(tags/tag/text(), 'Tenor')]">
        <xsl:value-of select="normalize-space(firstname)"/><xsl:text>~</xsl:text>
        <xsl:value-of select="normalize-space(lastname)"/>
        <xsl:if test="not(position() = last())"><xsl:text>, </xsl:text></xsl:if>
      </xsl:for-each>
Bass: <xsl:for-each select="members/memberGroup/member[contains(tags/tag/text(), 'Bass')]">
        <xsl:value-of select="normalize-space(firstname)"/><xsl:text>~</xsl:text>
        <xsl:value-of select="normalize-space(lastname)"/>
        <xsl:if test="not(position() = last())"><xsl:text>, </xsl:text></xsl:if>
      </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
