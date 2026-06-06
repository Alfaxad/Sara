Class Sara.REST.TaskBusinessService Extends Ens.BusinessService
{

Property TargetConfigNames As %String(MAXLEN = 1000) [ InitialExpression = "Sara.Interop.AgentProcess" ];

Parameter SETTINGS = "TargetConfigNames:Basic:selector?multiSelect=1&context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}";

Method OnProcessInput(
    pInput As %RegisteredObject,
    Output pOutput As %RegisteredObject) As %Status
{
    Set sc = $$$OK
    Try {
        For iTarget=1:1:$Length(..TargetConfigNames, ",") {
            Set target = $ZStrip($Piece(..TargetConfigNames, ",", iTarget), "<>W")
            Continue:target=""
            $$$ThrowOnError(..SendRequestSync(target, pInput, .pOutput, 90))
        }
    } Catch ex {
        Set sc = ex.AsStatus()
    }
    Quit sc
}

ClassMethod OnGetConnections(
    Output pArray As %String,
    pItem As Ens.Config.Item)
{
    Do ##super(.pArray, pItem)
    If pItem.GetModifiedSetting("TargetConfigNames", .targets) {
        For i=1:1:$Length(targets, ",") {
            Set target = $ZStrip($Piece(targets, ",", i), "<>W")
            Continue:target=""
            Set pArray(target) = ""
        }
    }
}

}
