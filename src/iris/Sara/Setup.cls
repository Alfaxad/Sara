Class Sara.Setup
{

ClassMethod Install(
    namespace As %String = "SARAFHIR",
    fhirWebApp As %String = "/fhir/r4",
    restWebApp As %String = "/sara/api",
    loadDemoData As %Boolean = 1,
    interactionsStrategy As %String(VALUELIST=",Json,JsonAdvSql") = "JsonAdvSql") As %Status
{
    Set sc = $$$OK
    Try {
        Write !,"Sara for IRIS install: namespace="_namespace_", fhir="_fhirWebApp_", rest="_restWebApp,!

        Set strategyClass = "HS.FHIRServer.Storage.JsonAdvSQL.InteractionsStrategy"
        If interactionsStrategy = "Json" {
            Set strategyClass = "HS.FHIRServer.Storage.Json.InteractionsStrategy"
        }

        Set metadataPackages = $lb("hl7.fhir.r4.core@4.0.1")

        ZN "HSLIB"
        Do ##class(HS.Util.Installer.Foundation).Install(namespace)

        ZN namespace
        Do ##class(HS.FHIRServer.Installer).InstallNamespace()
        If '##class(HS.FHIRServer.ServiceAdmin).EndpointExists(fhirWebApp) {
            Do ##class(HS.FHIRServer.Installer).InstallInstance(fhirWebApp, strategyClass, metadataPackages)
        }

        Set strategy = ##class(HS.FHIRServer.API.InteractionsStrategy).GetStrategyForEndpoint(fhirWebApp)
        Set config = strategy.GetServiceConfigData()
        Set config.DebugMode = 4
        Do strategy.SaveServiceConfigData(config)

        Do ..CreateRESTApplication(namespace, restWebApp)
        ZN namespace
        If ##class(%Dictionary.CompiledClass).%ExistsId("Sara.Interop.Production") {
            Do ##class(Ens.Director).SetAutoStart("Sara.Interop.Production")
        }

        If loadDemoData {
            Set demoDir = $System.Util.ManagerDirectory()_"sara-demo-fhir"
            Write !,"Loading Sara demo FHIR data from "_demoDir,!
            Set sc = ##class(HS.FHIRServer.Tools.DataLoader).SubmitResourceFiles(demoDir, "FHIRServer", fhirWebApp)
            If $$$ISERR(sc) {
                Write !,$System.Status.GetErrorText(sc),!
            }
        }
    } Catch ex {
        Set sc = ex.AsStatus()
    }
    Quit sc
}

ClassMethod CreateRESTApplication(namespace As %String, restWebApp As %String) As %Status
{
    ZN "%SYS"
    Set properties("NameSpace") = namespace
    Set properties("Enabled") = 1
    Set properties("AutheEnabled") = 32
    Set properties("DispatchClass") = "Sara.REST.TaskService"
    Set properties("ServeFiles") = 0
    Set properties("Recurse") = 0
    If ##class(Security.Applications).Exists(restWebApp) {
        Quit ##class(Security.Applications).Modify(restWebApp, .properties)
    }
    Quit ##class(Security.Applications).Create(restWebApp, .properties)
}

}
