param(
  [string]$Region = "ap-southeast-1",
  [string]$Cluster = "sentinel-cluster",
  [string]$ApiService = "sentinel-api",
  [string]$WorkerService = "sentinel-worker",
  [string]$BeatService = "sentinel-beat",
  [string]$PrivateSubnetA = "subnet-082732e10f66b75d4",
  [string]$PrivateSubnetB = "subnet-0df34e5c1bbfaae28",
  [string]$EcsSecurityGroup = "sg-05ab4136a1ddefbf9",
  [string]$AlbName = "sentinel-alb"
)

$ErrorActionPreference = "Stop"

Write-Host "== Preflight =="
$callerArn = aws sts get-caller-identity --region $Region --query "Arn" --output text
Write-Host "Caller ARN: $callerArn"

$clusterStatus = aws ecs describe-clusters --clusters $Cluster --region $Region --query "clusters[0].status" --output text
if ($clusterStatus -ne "ACTIVE") {
  throw "ECS cluster '$Cluster' is not ACTIVE (status: $clusterStatus)."
}
Write-Host "Cluster status: $clusterStatus"

$services = aws ecs describe-services `
  --cluster $Cluster `
  --services $ApiService $WorkerService $BeatService `
  --region $Region `
  --query "services[].{service:serviceName,status:status,desired:desiredCount,running:runningCount}" `
  --output table
Write-Host $services

Write-Host ""
Write-Host "== Run Alembic Migration Task =="
$svcDetail = aws ecs describe-services `
  --cluster $Cluster `
  --services $ApiService `
  --region $Region `
  --output json | ConvertFrom-Json

$awsvpc = $svcDetail.services[0].networkConfiguration.awsvpcConfiguration
if (-not $awsvpc) {
  throw "Could not read awsvpc network config from service '$ApiService'."
}

$subnetList = ($awsvpc.subnets -join ",")
$sgList = ($awsvpc.securityGroups -join ",")
$assignPublicIp = $awsvpc.assignPublicIp

if (-not $subnetList -or -not $sgList -or -not $assignPublicIp) {
  throw "Service network config is incomplete. Subnets='$subnetList' SGs='$sgList' AssignPublicIp='$assignPublicIp'"
}

$networkConfig = "awsvpcConfiguration={subnets=[$subnetList],securityGroups=[$sgList],assignPublicIp=$assignPublicIp}"
Write-Host "Using service network config:"
Write-Host "  subnets=[$subnetList]"
Write-Host "  securityGroups=[$sgList]"
Write-Host "  assignPublicIp=$assignPublicIp"

$runTaskJson = aws ecs run-task `
  --cluster $Cluster `
  --task-definition sentinel-api `
  --launch-type FARGATE `
  --network-configuration $networkConfig `
  --overrides file://infra/aws/ecs/run-migration-overrides.json `
  --region $Region `
  --output json | ConvertFrom-Json

if ($runTaskJson.failures -and $runTaskJson.failures.Count -gt 0) {
  $fail = $runTaskJson.failures[0]
  throw "Migration task failed to start. Reason: $($fail.reason) | ARN: $($fail.arn)"
}

$migTaskArn = $runTaskJson.tasks[0].taskArn
if (-not $migTaskArn) {
  throw "Migration task ARN is empty. Run-task did not return a task."
}

Write-Host "Migration task ARN: $migTaskArn"
aws ecs wait tasks-stopped --cluster $Cluster --tasks $migTaskArn --region $Region

$migExit = aws ecs describe-tasks `
  --cluster $Cluster `
  --tasks $migTaskArn `
  --region $Region `
  --query "tasks[0].containers[0].exitCode" `
  --output text

$migReason = aws ecs describe-tasks `
  --cluster $Cluster `
  --tasks $migTaskArn `
  --region $Region `
  --query "tasks[0].stoppedReason" `
  --output text

$migStream = aws ecs describe-tasks `
  --cluster $Cluster `
  --tasks $migTaskArn `
  --region $Region `
  --query "tasks[0].containers[0].logStreamName" `
  --output text

Write-Host "Migration exit code: $migExit"
Write-Host "Migration stopped reason: $migReason"
Write-Host "Migration log stream: $migStream"

if ($migStream -and $migStream -ne "None") {
  Write-Host ""
  Write-Host "Last 40 migration log lines:"
  aws logs get-log-events `
    --log-group-name /ecs/sentinel `
    --log-stream-name $migStream `
    --limit 40 `
    --region $Region `
    --query "events[].message" `
    --output text
}

if ("$migExit" -ne "0") {
  throw "Migration did not succeed (exit code: $migExit)."
}

Write-Host ""
Write-Host "== Rolling Services =="
aws ecs update-service --cluster $Cluster --service $ApiService --force-new-deployment --region $Region | Out-Null
aws ecs update-service --cluster $Cluster --service $WorkerService --force-new-deployment --region $Region | Out-Null
aws ecs update-service --cluster $Cluster --service $BeatService --force-new-deployment --region $Region | Out-Null

aws ecs wait services-stable --cluster $Cluster --services $ApiService --region $Region
aws ecs wait services-stable --cluster $Cluster --services $WorkerService --region $Region
aws ecs wait services-stable --cluster $Cluster --services $BeatService --region $Region

Write-Host "Services are stable."

$albDns = aws elbv2 describe-load-balancers `
  --names $AlbName `
  --region $Region `
  --query "LoadBalancers[0].DNSName" `
  --output text

Write-Host ""
Write-Host "== Outputs =="
Write-Host "ALB_DNS=$albDns"
Write-Host "MIGRATION_EXIT_CODE=$migExit"
Write-Host ""
Write-Host "Next: create CloudFront in front of this ALB, then use that CloudFront domain in Vercel env vars."
