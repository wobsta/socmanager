<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" />
    <xsl:template match="/">
      <xsl:variable name="from_year" select="number(substring-before(members/@info, '-'))"/>
      <xsl:variable name="to_year" select="number(substring-after(members/@info, '-'))"/>
      <xsl:text>männlich: </xsl:text>
      <xsl:value-of select="count(members/memberGroup/member[number(substring-after(substring-after(normalize-space(birthday), '.'), '.')) >= $from_year and
                                                             number(substring-after(substring-after(normalize-space(birthday), '.'), '.')) &lt;= $to_year and
                                                             normalize-space(gender) = 'male'])"/>
      <xsl:text>
weiblich: </xsl:text>
      <xsl:value-of select="count(members/memberGroup/member[number(substring-after(substring-after(normalize-space(birthday), '.'), '.')) >= $from_year and
                                                             number(substring-after(substring-after(normalize-space(birthday), '.'), '.')) &lt;= $to_year and
                                                             normalize-space(gender) = 'female'])"/>
      <xsl:text>
</xsl:text>
    </xsl:template>
</xsl:stylesheet>
