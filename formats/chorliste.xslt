<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" />
    <xsl:template match="/">
      <xsl:text>Sopran	Alt	Tenor	Bass
</xsl:text>
      <xsl:call-template name="iterate_parallel">
        <xsl:with-param name="l1" select="members/memberGroup/member[contains(tags/tag/text(), 'Sopran')]"/>
        <xsl:with-param name="l2" select="members/memberGroup/member[contains(tags/tag/text(), 'Alt')]"/>
        <xsl:with-param name="l3" select="members/memberGroup/member[contains(tags/tag/text(), 'Tenor')]"/>
        <xsl:with-param name="l4" select="members/memberGroup/member[contains(tags/tag/text(), 'Bass')]"/>
      </xsl:call-template>
    </xsl:template>
    <xsl:template name="iterate_parallel">
      <xsl:param name="l1"/>
      <xsl:param name="l2"/>
      <xsl:param name="l3"/>
      <xsl:param name="l4"/>
      <xsl:value-of select="normalize-space($l1[position()=1]/lastname)"/><xsl:text>, </xsl:text><xsl:value-of select="normalize-space($l1[position()=1]/firstname)"/><xsl:text>	</xsl:text>
      <xsl:value-of select="normalize-space($l2[position()=1]/lastname)"/><xsl:text>, </xsl:text><xsl:value-of select="normalize-space($l2[position()=1]/firstname)"/><xsl:text>	</xsl:text>
      <xsl:value-of select="normalize-space($l3[position()=1]/lastname)"/><xsl:text>, </xsl:text><xsl:value-of select="normalize-space($l3[position()=1]/firstname)"/><xsl:text>	</xsl:text>
      <xsl:value-of select="normalize-space($l4[position()=1]/lastname)"/><xsl:text>, </xsl:text><xsl:value-of select="normalize-space($l4[position()=1]/firstname)"/><xsl:text>
</xsl:text>
      <xsl:if test="count($l1)>1 or count($l2)>1 or count($l3)>1 or count($l4)>1">
         <xsl:call-template name="iterate_parallel">
           <xsl:with-param name="l1" select="$l1[position()>1]"/>
           <xsl:with-param name="l2" select="$l2[position()>1]"/>
           <xsl:with-param name="l3" select="$l3[position()>1]"/>
           <xsl:with-param name="l4" select="$l4[position()>1]"/>
         </xsl:call-template>
       </xsl:if>
    </xsl:template>
</xsl:stylesheet>
