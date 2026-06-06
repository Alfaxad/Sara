Class Sara.Message.TaskResponse Extends Ens.Response
{

Property Payload As %String(MAXLEN = "");
Property Summary As %String(MAXLEN = "");
Property Status As %String(MAXLEN = 64) [ InitialExpression = "ok" ];

}
