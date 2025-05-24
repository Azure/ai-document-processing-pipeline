param
(
    [Parameter(Mandatory = $true)]
    [string]$TenantId
)

Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

Write-Host "Installing VS Code..."
choco upgrade vscode -y --ignoredetectedreboot --force

Write-Host "Installing Azure CLI..."
choco upgrade azure-cli -y --ignoredetectedreboot --force

Write-Host "Installing Git..."
choco install git -y --ignoredetectedreboot --force

Write-Host "Installing Python 3.12..."
choco install python312 -y --ignoredetectedreboot --force

Write-Host "Installing Azure Developer CLI..."
choco install azd -y --ignoredetectedreboot --force
$env:Path += ";C:\Program Files\Azure Dev CLI"

Write-Host "Installing PowerShell Core..."
choco install powershell-core -y --ignoredetectedreboot --force

Write-Host "Installing GitHub Desktop..."
choco install github-desktop -y --ignoredetectedreboot --force

Write-Host "Installing Docker Desktop..."
choco install docker-desktop -y --ignoredetectedreboot --force

Write-Host "Updating Windows Subsystem for Linux..."
wsl --update

Write-Host "Downloading repository..."
mkdir C:\src
cd C:\src
git clone https://github.com/Azure/ai-document-processing-pipeline
cd .\ai-document-processing-pipeline\

Write-Host "Logging into the Azure CLI..."
az login --tenant $TenantId
azd auth login --tenant-id $TenantId

# Generate a .env file in the project folder in the virtual machine

azd provision --debug
azd up
