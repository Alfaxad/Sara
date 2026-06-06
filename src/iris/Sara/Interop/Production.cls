Class Sara.Interop.Production Extends Ens.Production
{

XData ProductionDefinition
{
<Production Name="Sara.Interop.Production" TestingEnabled="true" LogGeneralTraceEvents="true">
  <Description>Sara AI Agent for IRIS for Health FHIR, Embedded Python, and traceable Interoperability messages.</Description>
  <ActorPoolSize>2</ActorPoolSize>
  <Item Name="Sara.REST.TaskBusinessService" Category="Sara" ClassName="Sara.REST.TaskBusinessService" PoolSize="1" Enabled="true" Foreground="false" Comment="Receives REST-dispatched summary requests" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="TargetConfigNames">Sara.Interop.AgentProcess</Setting>
  </Item>
  <Item Name="Sara.Interop.AgentProcess" Category="Sara" ClassName="Sara.Interop.AgentProcess" PoolSize="1" Enabled="true" Foreground="false" Comment="Embedded Python smart summary agent" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="FHIRBaseURL">http://localhost:52773/fhir/r4</Setting>
    <Setting Target="Host" Name="FHIRUsername"></Setting>
    <Setting Target="Host" Name="FHIRPassword"></Setting>
  </Item>
  <Item Name="Sara.Interop.FHIRServerOperation" Category="Sara" ClassName="HS.FHIRServer.Interop.HTTPOperation" PoolSize="1" Enabled="true" Foreground="false" Comment="Traceable operation against the local IRIS FHIR Server" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="ServiceName">FHIRServer</Setting>
    <Setting Target="Host" Name="TraceOperations">*FULL*</Setting>
  </Item>
  <Item Name="HS.Util.Trace.Operations" Category="Sara" ClassName="HS.Util.Trace.Operations" PoolSize="1" Enabled="true" Foreground="false" Comment="FHIR trace viewer support" LogTraceEvents="true" Schedule="">
  </Item>
</Production>
}

}
