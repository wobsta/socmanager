<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" />
    <xsl:template match="tickets">
      <xsl:for-each select="ticket">
        <xsl:text>\ticket{</xsl:text>
        <xsl:value-of select="normalize-space(block)"/><xsl:text>}{</xsl:text>
        <xsl:value-of select="normalize-space(row)"/><xsl:text>}{</xsl:text>
        <xsl:value-of select="normalize-space(seat)"/><xsl:text>}{</xsl:text>
        <xsl:value-of select="normalize-space(cathegory)"/><xsl:text>}{</xsl:text>
        <xsl:value-of select="normalize-space(regular)"/><xsl:text>}%
</xsl:text>
      </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
