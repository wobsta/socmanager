<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output indent="yes"/>
<xsl:template match="/">
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.008.003.02" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:iso:std:iso:20022:tech:xsd:pain.008.003.02 pain.008.003.02.xsd">
  <CstmrDrctDbtInitn>
    <GrpHdr>
      <MsgId>Eintrittskarten</MsgId>
      <CreDtTm><xsl:value-of select="debits/now"/></CreDtTm>
      <NbOfTxs><xsl:value-of select="debits/count"/></NbOfTxs>
      <InitgPty>
        <Nm>Schwäbischer Oratorienchor e.V.</Nm>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>Eintrittskarten</PmtInfId>
      <PmtMtd>DD</PmtMtd>
      <BtchBooking>false</BtchBooking>
      <NbOfTxs><xsl:value-of select="debits/count"/></NbOfTxs>
      <CtrlSum><xsl:value-of select="debits/total"/>.00</CtrlSum>
      <PmtTpInf>
        <SvcLvl>
          <Cd>SEPA</Cd>
        </SvcLvl>
        <LclInstrm>
          <Cd>CORE</Cd>
        </LclInstrm>
        <SeqTp>OOFF</SeqTp>
      </PmtTpInf>
      <ReqdColltnDt><xsl:value-of select="debits/now_plus_ten"/></ReqdColltnDt>
      <Cdtr>
        <Nm>Schwäbischer Oratorienchor e.V.</Nm>
      </Cdtr>
      <CdtrAcct>
        <Id>
          <IBAN>DE36720501010030209605</IBAN>
        </Id>
      </CdtrAcct>
      <CdtrAgt>
        <FinInstnId>
          <BIC>BYLADEM1AUG</BIC>
        </FinInstnId>
      </CdtrAgt>
      <ChrgBr>SLEV</ChrgBr>
      <CdtrSchmeId>
        <Id>
          <PrvtId>
            <Othr>
              <Id>DE95ZZZ00001496812</Id>
              <SchmeNm>
                <Prtry>SEPA</Prtry>
              </SchmeNm>
            </Othr>
          </PrvtId>
        </Id>
      </CdtrSchmeId>
      <xsl:for-each select="debits/debit">
      <DrctDbtTxInf>
        <PmtId>
          <EndToEndId><xsl:value-of select="id"/></EndToEndId>
        </PmtId>
        <InstdAmt Ccy="EUR"><xsl:value-of select="amount"/>.00</InstdAmt>
        <DrctDbtTx>
          <MndtRltdInf>
            <MndtId><xsl:value-of select="id"/>-<xsl:value-of select="bankcode"/></MndtId>
            <DtOfSgntr><xsl:value-of select="date"/></DtOfSgntr>
          </MndtRltdInf>
        </DrctDbtTx>
        <DbtrAgt>
          <FinInstnId>
            <BIC><xsl:value-of select="account_bic"/></BIC>
          </FinInstnId>
        </DbtrAgt>
        <Dbtr>
          <Nm><xsl:value-of select="account_holder"/></Nm>
        </Dbtr>
        <DbtrAcct>
          <Id>
            <IBAN><xsl:value-of select="account_iban"/></IBAN>
          </Id>
        </DbtrAcct>
        <UltmtDbtr>
          <Nm><xsl:value-of select="account_holder"/></Nm>
        </UltmtDbtr>
        <RmtInf>
          <Ustrd>Eintrittskarten Kauf-ID <xsl:value-of select="id"/></Ustrd>
        </RmtInf>
      </DrctDbtTxInf>
      </xsl:for-each>
    </PmtInf>
  </CstmrDrctDbtInitn>
</Document>
</xsl:template>
</xsl:stylesheet>
