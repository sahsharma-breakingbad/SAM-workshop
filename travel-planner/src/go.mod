module travel-planner

go 1.26

require github.com/SolaceDev/solace-agent-mesh-go/pkg/samtoolsdk v0.0.0

// bundled SDK
replace github.com/SolaceDev/solace-agent-mesh-go/pkg/samtoolsdk => ./_sdk/samtoolsdk
