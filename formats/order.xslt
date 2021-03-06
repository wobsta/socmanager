<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" />
    <xsl:template match="/">
      <xsl:for-each select="members/memberGroup">
        <xsl:for-each select="member">
          <xsl:value-of select="normalize-space(firstname)"/><xsl:text> </xsl:text><xsl:value-of select="normalize-space(lastname)"/><xsl:text>, </xsl:text>
        </xsl:for-each>
        <xsl:value-of select="normalize-space(member[1]/street)"/><xsl:text>, </xsl:text>
        <xsl:value-of select="normalize-space(member[1]/zip)"/><xsl:text> </xsl:text><xsl:value-of select="normalize-space(member[1]/city)"/>

        <xsl:for-each select="member">
          <xsl:text>
Kontakt</xsl:text>
          <xsl:if test="count(../member) > 1"><xsl:text> </xsl:text><xsl:value-of select="normalize-space(firstname)"/></xsl:if>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(email)"/><xsl:text>, </xsl:text>
          <xsl:value-of select="normalize-space(phone)"/>
        </xsl:for-each>
<xsl:text>

</xsl:text>
      </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
