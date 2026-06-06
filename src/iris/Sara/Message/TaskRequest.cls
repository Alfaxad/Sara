Class Sara.Message.TaskRequest Extends Ens.Request
{

Property PatientId As %String(MAXLEN = 128);
Property Role As %String(MAXLEN = 64) [ InitialExpression = "ed_clinician" ];
Property Payload As %String(MAXLEN = "");

}
