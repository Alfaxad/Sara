Class Sara.Interop.AgentProcess Extends Ens.BusinessProcess
{

Property FHIRBaseURL As %String(MAXLEN = 512);
Property FHIRUsername As %String(MAXLEN = 128);
Property FHIRPassword As %String(MAXLEN = 512);

Parameter SETTINGS = "FHIRBaseURL:Basic,FHIRUsername:Basic,FHIRPassword:Basic:password";

Method OnRequest(
    request As Sara.Message.TaskRequest,
    Output response As Sara.Message.TaskResponse) As %Status
{
    Set sc = $$$OK
    Set response = ##class(Sara.Message.TaskResponse).%New()
    Try {
        $$$TRACE("Sara Embedded Python agent starting for patient "_request.PatientId)
        Set sys = ##class(%SYS.Python).Import("sys")
        Set pythonPath = $System.Util.ManagerDirectory()_"sara-python"
        If 'sys.path."__contains__"(pythonPath) {
            Do sys.path.insert(0, pythonPath)
        }
        Set py = ##class(%SYS.Python).Import("sara_iris.agent")
        Set builtins = ##class(%SYS.Python).Import("builtins")
        Set result = builtins.getattr(py, "run_task_json")."__call__"(request.Payload, request.PatientId, request.Role, ..FHIRBaseURL, ..FHIRUsername, ..FHIRPassword)
        Set response.Payload = result
        Set response.Summary = result
        Set response.Status = "ok"
        $$$TRACE("Sara Embedded Python agent completed")
    } Catch ex {
        Set sc = ex.AsStatus()
        Set response.Status = "error"
        Set response.Payload = "{""error"":""Sara Embedded Python failure""}"
    }
    Quit sc
}

}
