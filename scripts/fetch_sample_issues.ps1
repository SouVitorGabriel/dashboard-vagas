param(
    [string]$Owner = "backend-br",
    [string]$Repo = "vagas",
    [ValidateSet("all", "open", "closed")]
    [string]$State = "all",
    [int]$Limit = 100,
    [string]$Output = "data/issues_sample_raw.json"
)

$headers = @{
    "User-Agent" = "pi4-vagas-prototype"
    "Accept" = "application/vnd.github+json"
}

if ($env:GITHUB_TOKEN) {
    $headers["Authorization"] = "Bearer $($env:GITHUB_TOKEN)"
}

$allIssues = @()
$page = 1

while ($allIssues.Count -lt $Limit) {
    $remaining = $Limit - $allIssues.Count
    $perPage = [Math]::Min(100, [Math]::Max(1, $remaining))
    $uri = "https://api.github.com/repos/$Owner/$Repo/issues?state=$State&sort=created&direction=desc&per_page=$perPage&page=$page"

    $batch = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
    if (-not $batch -or $batch.Count -eq 0) {
        break
    }

    $issuesOnly = $batch | Where-Object { -not $_.pull_request }
    $allIssues += $issuesOnly
    $page += 1
}

if ($allIssues.Count -gt $Limit) {
    $allIssues = $allIssues | Select-Object -First $Limit
}

$outputDir = Split-Path -Path $Output -Parent
if ($outputDir) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$allIssues | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $Output
Write-Output "Saved $($allIssues.Count) issues to $Output"
