import os, sys, json
import utils

deployment_name = "aoai-gateway-02" # change the name to match your naming style
resource_group_name = f"lab-{deployment_name}" # change the name to match your naming style
resource_group_location = "eastasia"

apim_sku = 'Basicv2'

# Prioritize East US until exhaustion (simulate PTU with TPM), then equally distribute between Sweden and West US (consumption fallback)
openai_resources = [
    {"name": "openai1", "location": "canadaeast", "priority": 1},
    {"name": "openai2", "location": "uksouth", "priority": 2, "weight": 50},
    {"name": "openai3", "location": "spaincentral", "priority": 2, "weight": 50}
]

openai_deployment_name = "gpt-4.1-api"  # change the name to match your naming style
openai_model_name = "gpt-4.1"
openai_model_version = "2025-04-14"
openai_model_capacity = 500
openai_model_sku = 'GlobalStandard'
openai_api_version = "2024-10-21"

utils.print_ok('Notebook initialized')

output = utils.run("az account show", "Retrieved az account", "Failed to get the current az account")

if output.success and output.json_data:
    current_user = output.json_data['user']['name']
    tenant_id = output.json_data['tenantId']
    subscription_id = output.json_data['id']

    utils.print_info(f"Current user: {current_user}")
    utils.print_info(f"Tenant ID: {tenant_id}")
    utils.print_info(f"Subscription ID: {subscription_id}")

# Create the resource group if doesn't exist
utils.create_resource_group(resource_group_name, resource_group_location)

# Define the Bicep parameters
bicep_parameters = {
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {
        "apimSku": { "value": apim_sku },
        "openAIConfig": { "value": openai_resources },
        "openAIDeploymentName": { "value": openai_deployment_name },
        "openAIModelName": { "value": openai_model_name },
        "openAIModelVersion": { "value": openai_model_version },
        "openAIModelCapacity": { "value": openai_model_capacity },
        "openAIModelSKU": { "value": openai_model_sku },
        "openAIAPIVersion": { "value": openai_api_version }
    }
}

# Write the parameters to the params.json file
with open('params.json', 'w') as bicep_parameters_file:
    bicep_parameters_file.write(json.dumps(bicep_parameters))

# Run the deployment
output = utils.run(f"az deployment group create --name {deployment_name} --resource-group {resource_group_name} --template-file main.bicep --parameters params.json",
    f"Deployment '{deployment_name}' succeeded", f"Deployment '{deployment_name}' failed")

# Obtain all of the outputs from the deployment
output = utils.run(f"az deployment group show --name {deployment_name} -g {resource_group_name}", f"Retrieved deployment: {deployment_name}", f"Failed to retrieve deployment: {deployment_name}")

if output.success and output.json_data:
    apim_service_id = utils.get_deployment_output(output, 'apimServiceId', 'APIM Service Id')
    apim_resource_gateway_url = utils.get_deployment_output(output, 'apimResourceGatewayURL', 'APIM API Gateway URL')
    apim_subscription_key = utils.get_deployment_output(output, 'apimSubscriptionKey', 'APIM Subscription Key (masked)', True)