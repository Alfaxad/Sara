Class Sara.REST.TaskService Extends %CSP.REST
{

Parameter CHARSET = "UTF-8";
Parameter CONVERTINPUTSTREAM = 1;
Parameter HandleCorsRequest = 1;

XData UrlMap [ XMLNamespace = "http://www.intersystems.com/urlmap" ]
{
<Routes>
  <Route Url="/health" Method="GET" Call="Health" Cors="true"/>
  <Route Url="/summary" Method="POST" Call="Summary" Cors="true"/>
  <Route Url="/evidence" Method="GET" Call="Evidence" Cors="true"/>
</Routes>
}

ClassMethod Health() As %Status
{
    Set %response.ContentType = "application/json"
    Set body = ##class(%DynamicObject).%New()
    Do body.%Set("status", "ok")
    Do body.%Set("service", "Sara for IRIS")
    Do body.%Set("production", "Sara.Interop.Production")
    Do body.%Set("fhirEndpoint", "/fhir/r4")
    Write body.%ToJSON()
    Quit $$$OK
}

ClassMethod Evidence() As %Status
{
    Set %response.ContentType = "application/json"
    Set body = ##class(%DynamicObject).%New()
    Do body.%Set("production", "Sara.Interop.Production")
    Do body.%Set("embeddedPython", "Sara.Interop.AgentProcess")
    Do body.%Set("fhirServer", "/fhir/r4")
    Do body.%Set("messageViewer", "Interoperability > View > Messages")
    Do body.%Set("sqlBuilder", "See artifact irisEvidence.sqlBuilder.sql")
    Write body.%ToJSON()
    Quit $$$OK
}

ClassMethod Summary() As %Status
{
    Set %response.ContentType = "application/json"
    Set parseOk = 1
    Try {
        Set payload = {}.%FromJSON(%request.Content)
    } Catch ex {
        Set parseOk = 0
    }
    If 'parseOk {
        Do ..WriteError(..#HTTP400BADREQUEST, "Invalid JSON request body")
        Quit $$$OK
    }

    Set request = ##class(Sara.Message.TaskRequest).%New()
    Set request.PatientId = payload.%Get("patientId", "sara-demo-patient")
    Set request.Role = payload.%Get("role", "ed_clinician")
    Set request.Payload = payload.%ToJSON()

    Set sc = $$$OK
    Try {
        $$$ThrowOnError(##class(Ens.Director).CreateBusinessService("Sara.REST.TaskBusinessService", .service))
        $$$ThrowOnError(service.ProcessInput(request, .response))
    } Catch ex {
        Set sc = ex.AsStatus()
    }

    If $$$ISERR(sc) {
        Do ..WriteError(..#HTTP500INTERNALSERVERERROR, "Sara production request failed", $System.Status.GetErrorText(sc))
        Quit $$$OK
    }

    If '$IsObject(response) {
        Do ..WriteError(..#HTTP500INTERNALSERVERERROR, "Sara production returned no response")
        Quit $$$OK
    }

    Write response.Payload
    Quit $$$OK
}

ClassMethod WriteError(statusCode As %Integer, error As %String, details As %String = "")
{
    Set %response.Status = statusCode
    Set body = ##class(%DynamicObject).%New()
    Do body.%Set("error", error)
    If details '= "" {
        Do body.%Set("details", details)
    }
    Write body.%ToJSON()
    Quit
}

}
