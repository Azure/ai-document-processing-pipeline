@description('Name of the resource.')
param name string
@description('Location to deploy the resource. Defaults to the location of the resource group.')
param location string = resourceGroup().location
@description('Tags for the resource.')
param tags object = {}

@description('Security rules of the network security group.')
param securityRules object[] = []

// Deployments

resource networkSecurityGroup 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    securityRules: securityRules
  }
}

// Outputs

@description('ID for the deployed Network Security Group resource.')
output id string = networkSecurityGroup.id
@description('Name for the deployed Network Security Group resource.')
output name string = networkSecurityGroup.name
