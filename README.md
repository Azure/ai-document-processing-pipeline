---
name: Azure AI Document Processing Pipeline using Python Durable Functions
description: A customizable template for building and deploying AI-powered document processing pipelines using Durable Functions orchestrations, incorporating Azure AI services and Azure OpenAI LLMs.
languages:
  - python
  - bicep
  - azdeveloper
  - powershell
products:
  - azure
  - ai-services
  - azure-openai
  - document-intelligence
  - azure-blob-storage
  - azure-queue-storage
  - azure-container-apps
  - azure-app-configuration
  - azure-container-registry
  - azure-key-vault
page_type: sample
urlFragment: azure-ai-document-processing-pipeline-python
---

# Azure AI Document Processing Pipeline using Python Durable Functions

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jamesmcroft/azure-ai-document-pipeline-python-sample?quickstart=1)

This project is a customizable template for building and deploying AI-powered document processing pipelines using Durable Functions orchestrations, incorporating Azure AI services and Azure OpenAI LLMs. It provides a variety of serverless Function activities for document classification and structured data extraction to make it easy to build reliable and accurate workflows to solve complex document processing challenges. If you're looking to automate document processing tasks with AI, this project is a great starting point.

## Table of Contents

- [Why use this project?](#why-use-this-project)
- [Key features](#key-features)
- [Understanding the Pipeline](#understanding-the-pipeline)
  - [Flow](#flow)
  - [Python Pipeline Specifics](#python-pipeline-specifics)
  - [Azure Services](#azure-services)
- [Example pipeline output](#example-pipeline-output)
- [Pre-built Classification & Extraction Scenarios](#pre-built-classification--extraction-scenarios)
- [Additional Use Cases](#additional-use-cases)
- [Development Environment](#development-environment)
  - [Setup on GitHub Codespaces](#setup-on-github-codespaces)
  - [Setup on Local Machine](#setup-on-local-machine)
- [Deployment](#deployment)
  - [Deploying to Azure](#deploying-to-azure)
  - [Running the application locally](#running-the-application-locally)
  - [Testing the pre-built pipeline](#testing-the-pre-built-pipeline)
    - [Via the HTTP Trigger](#via-the-http-trigger)
    - [Via the Azure Storage queue](#via-the-azure-storage-queue)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## Why use this project?

Many organizations are looking to automate manual document processing tasks that are time-consuming and error-prone. While it is possible to automate these tasks using existing tools and services, they often require significant effort to set up and maintain.

Large language models have emerged as a powerful tool for general-purpose document processing tasks, able to handle any variety of document type and structure. Utilizing models with multimodal capabilities, such as Azure OpenAI's GPT-4o, enhances the accuracy and reliability of classifying and extracting structure data from documents by incorporating both text and image data.

This project provides the techniques and patterns to combine the capabilities of traditional OCR analysis with the power of LLMs to build a robust document processing pipeline.

## Key features

- [**Durable Functions orchestration**](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview?tabs=in-process%2Cnodejs-v3%2Cv1-model&pivots=python): The project uses Durable Functions to orchestrate the document processing pipeline, allowing for stateful workflows and parallel processing of documents.
- [**Scalable containerized hosting**](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deploy-container-apps?tabs=acr%2Cbash&pivots=programming-language-python): The project is designed to be deployed as a containerized application using Azure Container Apps, allowing for easy scaling and management of the document processing pipeline.
- **Document data processing**: Many of the core activites for document processing are included by default, and require minimal configuration to customize to your use cases. These include:
  - [**Document data classifier**](./src/AIDocumentPipeline/documents/services/document_data_classifier.py): A service that uses Azure OpenAI's GPT-4o model to classify documents based on their content. This service can be used to classify documents into any categories you define.
  - [**Document data extractor**](./src/AIDocumentPipeline/documents/services/document_data_extractor.py): A service that combines Azure OpenAI's GPT-4o model with Azure AI Document Intelligence to extract structured data from documents using a multimodal approach, combining text and images. This service can be used to extract any structured data you define from documents using Pydantic models to define the expected output schema.
- **Model confidence scores**: Combining Azure AI Document Intelligence's model internal confidence scores with Azure OpenAI's GPT-4o `logprobs` and structured outputs features, the pipeline is able to provide a confidence score for the overall document classification and extraction process. This allows you to validate the accuracy of the results and take action if the confidence score is below a certain threshold, such as sending alerts or raising exceptions for human review.
- **Data validation**: Data is validated at every step of the process, including sub-orchestrations, ensuring that you not only receive the final output, but also the intermediate data at every step of the process.
- **OpenTelemetry**: The pipeline is configured to also support OpenTelemetry for gathering logs, metrics, and traces of the pipeline. This allows for easy monitoring and debugging of the pipeline, as well as integration with Azure Monitor and other observability tools.
- **Flexible configuration**: Using Durable Functions and separating out concerns to individual activities, the pipeline can be easily configured to support any document processing use case. The modular and extensible approach allows you to add or remove activities as needed.
- **Secure by default**: Azure Managed Identity and Azure RBAC least privilege access is used to secure the pipeline and ensure that only authorized services can access the Azure resources used in the pipeline. Additionally, opt-in to deploying the infrastructure using zero-trust principles with virtual networks and private endpoints to isolate the Azure resources from the public internet.
- **Infrastructure-as-code**: Azure Bicep modules and PowerShell deployment scripts are provided to define the Azure infrastructure for the document processing pipeline, allowing for easy deployment and management of the resources required.

## Understanding the Pipeline

![Azure AI Document Processing Pipeline](./assets/Flow.png)

This approach takes advantage of the following techniques for document data processing:

- [Document Classification with Azure OpenAI's GPT-4o Vision Capabilities](https://github.com/Azure-Samples/azure-ai-document-processing-samples/blob/main/samples/python/classification/document-classification-gpt-vision.ipynb)
- [Document Extraction using Multi-Modal (Text and Vision) Capabilities combining Azure AI Document Intelligence and Azure OpenAI's GPT-4o](https://github.com/Azure-Samples/azure-ai-document-processing-samples/blob/main/samples/python/extraction/multimodal/document-extraction-gpt-text-and-vision.ipynb)

### Flow

The pipeline is implemented using Durable Functions and consists of the following steps:

- Upload a batch of documents to an Azure Storage blob container.
- Once the documents are uploaded, send a message to the Azure Storage queue containing the container reference to trigger the document processing pipeline.
- The **[Process Document Batch workflow](./src/AIDocumentPipeline/documents/workflows/process_document_batch_workflow.py)** picks up the message from the queue and starts to process the request.
- Firstly, the batch document folders are retrieved from the blob container using the container reference in the message. **See [Get Document Folders](./src/AIDocumentPipeline/documents/activities/get_document_folders.py).**
  - _Note: Access to the Azure Storage account is established via a user-assigned managed identity when deployed in Azure_.
- The initial workflow then triggers the specific document processing workflow for each document folder in the batch in parallel using the **[Process Document workflow](./src/AIDocumentPipeline/documents/workflows/process_document_workflow.py)**. These process the folders as follows:
  - For each folder in the batch:
    - For each file in the folder:
      - Run the [`ClassifyDocument` activity](./src/AIDocumentPipeline/documents/activities/classify_document.py) to classify the content of the file using the [document data classifier service](./src/AIDocumentPipeline/documents/services/document_data_classifier.py), validating the classification against a pre-defined list in the pipeline.
      - If the classification is a valid extraction type, use the [document data extraction service](./src/AIDocumentPipeline/documents/services/document_data_extractor.py) using the Azure OpenAI GPT-4o model and the [strict Structured Outputs feature](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/structured-outputs?tabs=python-secure%2Cdotnet-entra-id&pivots=programming-language-python) to extract data based on a JSON schema of a type.
        - In this example, the classification and extraction is setup for invoices, as defined in the [Invoice schema object](./src/AIDocumentPipeline/invoices/models/invoice.py). The invoice data is extracted using the [Invoice extraction activity](./src/AIDocumentPipeline/invoices/activities/extract_invoice.py) which uses the [document data extractor service](./src/AIDocumentPipeline/documents/services/document_data_extractor.py) to extract the data from the document.

Before continuing with this project, please ensure that you have understanding of the following concepts:

### Python Pipeline Specifics

- [Durable Functions](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview?tabs=in-process%2Cnodejs-v3%2Cv1-model&pivots=python)
- [Using Blueprints in Azure Functions for modular components](https://learn.microsoft.com/en-gb/azure/azure-functions/functions-reference-python?tabs=get-started%2Casgi%2Capplication-level&pivots=python-mode-decorators#blueprints)
- [Azure Functions as Containers](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deploy-container-apps?tabs=acr%2Cbash&pivots=programming-language-python)

### Azure Services

- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deploy-container-apps?tabs=acr%2Cbash&pivots=programming-language-csharp), used to host the containerized functions used in the document processing pipeline.
  - **Note**: By containerizing the functions app, you can integrate this specific orchestration pipeline into an existing microservices architecture or deploy it as a standalone service.
- [Azure AI Services](https://learn.microsoft.com/en-us/azure/ai-services/what-are-ai-services), a managed service for all Azure AI Services, including Azure OpenAI, deploying the latest GPT-4o model to support vision-based extraction techniques.
  - [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview)
  - [Azure AI Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
  - **Note**: The GPT-4o model is not available in all Azure OpenAI regions. For more information, see the [Azure OpenAI Service documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#standard-deployment-model-availability).
- [Azure Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-introduction), used to store the batch of documents to be processed and the extracted data from the documents. The storage account is also used to store the queue messages for the document processing pipeline.
- [Azure Storage Queues](https://learn.microsoft.com/en-us/azure/storage/queues/storage-queues-introduction), used to trigger the Durable Functions workflow for the document processing pipeline. The queue messages contain the container reference to the batch of documents to be processed.
  - **Note**: This component can be replaced with any trigger mechanism you desire that is supported by Azure Functions, including Azure Service Bus, Event Grid, or HTTP triggers.
- [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/overview), used to store logs and traces from the document processing pipeline for monitoring and troubleshooting purposes.
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-intro), used to store the container images for the document processing pipeline service that will be consumed by Azure Container Apps.
- [Azure User-Assigned Managed Identity](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview-for-developers?tabs=portal%2Cdotnet), used to authenticate the service deployed in the Azure Container Apps environment to securely access other Azure services without key-based authentication, including the Azure Storage account and Azure OpenAI service.
- [Azure Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview?tabs=bicep), used to create a repeatable infrastructure deployment for the Azure resources.

## Example pipeline output

Below is an example [invoice](./tests/InvoiceBatch/SharpConsulting/2024-05-16.pdf) that needs to be processed by the [document processing pipeline](./src/AIDocumentPipeline/documents/workflows/process_document_workflow.py). By combining the document's text from the Azure AI Document Intelligence `prebuilt-layout` analysis with the document page images using the Azure OpenAI GPT-4o model, the pipeline is able to extract structured data from the document with high accuracy and confidence. For more information on how the confidence scores are calculated, see the [FAQ](#how-are-confidence-scores-calculated) section.

![Example Invoice](./assets/Invoice.png)

```json
{
  "data": {
    "customer_name": "Sharp Consulting",
    "customer_tax_id": null,
    "customer_address": {
      "street": "73 Regal Way",
      "city": "Leeds",
      "state": null,
      "postal_code": "LS1 5AB",
      "country": "UK"
    },
    "shipping_address": null,
    "purchase_order": "15931",
    "invoice_id": "3847193",
    "invoice_date": null,
    "due_date": "2024-05-24",
    "vendor_name": "NEXGEN",
    "vendor_address": null,
    "vendor_tax_id": null,
    "remittance_address": null,
    "subtotal": null,
    "total_discount": null,
    "total_tax": null,
    "invoice_total": {
      "currency_code": "GBP",
      "amount": 293.52
    },
    "payment_term": null,
    "items": [
      {
        "product_code": "MA197",
        "description": "STRETCHWRAP ROLL",
        "quantity": 5,
        "tax": null,
        "unit_price": {
          "currency_code": "GBP",
          "amount": 16.62
        },
        "total": {
          "currency_code": "GBP",
          "amount": 83.1
        }
      },
      {
        "product_code": "ST4086",
        "description": "BALLPOINT PEN MED.",
        "quantity": 10,
        "tax": null,
        "unit_price": {
          "currency_code": "GBP",
          "amount": 2.49
        },
        "total": {
          "currency_code": "GBP",
          "amount": 24.9
        }
      },
      {
        "product_code": "JF9912413BF",
        "description": "BUBBLE FILM ROLL CL.",
        "quantity": 12,
        "tax": null,
        "unit_price": {
          "currency_code": "GBP",
          "amount": 15.46
        },
        "total": {
          "currency_code": "GBP",
          "amount": 185.52
        }
      }
    ]
  },
  "overall_confidence": 0.9886610106263585
}
```

## Pre-built Classification & Extraction Scenarios

The accelerator comes with a pre-built [document processing pipeline](./src/AIDocumentPipeline/documents/workflows/process_document_workflow.py) that will take the folders in an Azure Storage blob container and process each document. It will first classify the document into one of the defined categories in the pipeline, and then extract the structured data from the document using the Azure OpenAI GPT-4o model with multimodal capabilities.

The pipeline is currently configured to process the following document types:

| Document Type                                                                  | Description                                                                                                                                                  |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [**Invoice**](./src/AIDocumentPipeline/invoices/activities/extract_invoice.py) | Using a [structured Invoice object](./src/AIDocumentPipeline/invoices/models/invoice.py), invoice documents can be extracted into a standard Invoice schema. |

The classification and extraction processes can be customized to suit your needs, either by modifying the existing code, or introducing new document types and workflows.

## Additional Use Cases

The pipeline can be extended to support any document processing use case, including:

- **Contracts**: Use natural language rules to extract inferred data points from clauses, such as exit dates, renewal terms, and other key information.
- **Bounded/continuous documents**: Ingest single PDFs that contain one or more documents, also known as continuous documents, detect the boundaries of each using classification techniques, and perform extractions on each sub-document.
- **General documents**: Regardless of the document type and format, whether PDF, Word, or scanned image, extract structured data from the files into your own defined schema.

## Development Environment

The repository contains a [devcontainer](./.devcontainer/README.md) that contains all the necessary tools and dependencies to run the application, and deploy the Azure infrastructure.

### Setup on GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jamesmcroft/azure-ai-document-pipeline-python-sample?quickstart=1)

> [!NOTE]
> After the environment has loaded, you may need to run the following command in the terminal to install the necessary Python dependencies: `pip --disable-pip-version-check --no-cache-dir install --user -r src/AIDocumentPipeline/requirements.txt`

Once the Dev Container is up and running, continue to the [deployment](#deployment) section.

### Setup on Local Machine

To use the Dev Container, you need to have the following tools installed on your local machine:

- Install [**Visual Studio Code**](https://code.visualstudio.com/download)
- Install [**Docker Desktop**](https://www.docker.com/products/docker-desktop)
- Install [**Remote - Containers**](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension for Visual Studio Code

To setup a local development environment, follow these steps:

> [!IMPORTANT]
> Ensure that Docker Desktop is running on your local machine.

1. Clone the repository to your local machine.
2. Open the repository in Visual Studio Code.
3. Press `F1` to open the command palette and type `Dev Containers: Reopen in Container`.

> [!NOTE]
> After the environment has loaded, you may need to run the following command in the terminal to install the necessary Python dependencies: `pip --disable-pip-version-check --no-cache-dir install --user -r src/AIDocumentPipeline/requirements.txt`

Once the Dev Container is up and running, continue to the [deployment](#deployment) section.

## Deployment

The sample project is designed to be deployed as a containerized application using Azure Container Apps. The deployment is defined using Azure Bicep in the [infra folder](./infra/).

The deployment is split into two parts, run by separate scripts using the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli):

- **[Core Infrastructure](./infra/core.bicep)**: Deploys all of the necessary core components that are required for the document processing pipeline, including the Azure AI services, Azure Storage account, Azure Container Registry, and Azure Container Apps environment. See **Deploy Core Infrastructure** [PowerShell script](./infra/scripts/Deploy-Infrastructure.ps1) or [Bash script](./infra/scripts/deploy_infrastructure.sh) for deployment via CLI.
- **[Application Deployment](./infra/apps/AIDocumentPipeline/app.bicep)**: Deploys the containerized application to the Azure Container Apps environment. See **Deploy App** [PowerShell script](./infra/scripts/Deploy-App.ps1) or [Bash script](./infra/scripts/deploy_app.sh) for deployment via CLI.

> [!IMPORTANT]
> The deployment can be configured to your specific needs by modifying the parameters in the [./infra/core.bicepparam](./infra/core.bicepparam) file, or using defined system environment variables (see below). All parameters are optional, and if not provided, resources will be deployed using the naming conventions defined in the Azure Cloud Adoption Framework.

<details>
  <summary><strong>Environment Variables</strong></summary>

| Environment Variable                           | Description                                                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| AZURE_ENV_NAME                                 | Name of the Azure environment to deploy.                                                                           |
| AZURE_LOCATION                                 | Azure region to deploy the resources, e.g. eastus.                                                                 |
| AZURE_RESOURCE_GROUP_NAME                      | Name of the Azure Resource Group to deploy the resources, e.g. document-processing-rg.                             |
| AZURE_PRINCIPAL_ID                             | The Azure Principal ID of an Entra ID user to assign RBAC roles to, e.g. 12345678-1234-1234-1234-123456789012.     |
| AZURE_NETWORK_ISOLATION                        | Whether to deploy the resources in a private virtual network with private endpoints, e.g. true.                    |
| CONTAINER_REGISTRY_REUSE                       | Whether to reuse an existing Container Registry, e.g. false.                                                       |
| CONTAINER_REGISTRY_RESOURCE_GROUP_NAME         | Name of the Azure Resource Group for the Container Registry to reuse, e.g. container-registry-rg.                  |
| CONTAINER_REGISTRY_NAME                        | Name of the Azure Container Registry, e.g. container-registry.                                                     |
| LOG_ANALYTICS_WORKSPACE_REUSE                  | Whether to reuse an existing Log Analytics Workspace, e.g. false.                                                  |
| LOG_ANALYTICS_WORKSPACE_RESOURCE_GROUP_NAME    | Name of the Azure Resource Group for the Log Analytics Workspace to reuse, e.g. log-analytics-rg.                  |
| LOG_ANALYTICS_WORKSPACE_NAME                   | Name of the Azure Log Analytics Workspace, e.g. log-analytics-workspace.                                           |
| APP_INSIGHTS_REUSE                             | Whether to reuse an existing Application Insights resource, e.g. false.                                            |
| APP_INSIGHTS_RESOURCE_GROUP_NAME               | Name of the Azure Resource Group for the Application Insights resource to reuse, e.g. app-insights-rg.             |
| APP_INSIGHTS_NAME                              | Name of the Azure Application Insights resource, e.g. app-insights.                                                |
| AZURE_AI_SERVICES_REUSE                        | Whether to reuse an existing Azure AI Services resource, e.g. false.                                               |
| AZURE_AI_SERVICES_RESOURCE_GROUP_NAME          | Name of the Azure Resource Group for the Azure AI Services resource to reuse, e.g. ai-services-rg.                 |
| AZURE_AI_SERVICES_NAME                         | Name of the Azure AI Services resource, e.g. ai-services.                                                          |
| AZURE_DB_REUSE                                 | Whether to reuse an existing Azure Cosmos DB account, e.g. false.                                                  |
| AZURE_DB_RESOURCE_GROUP_NAME                   | Name of the Azure Resource Group for the Azure Cosmos DB account to reuse, e.g. cosmos-db-rg.                      |
| AZURE_DB_ACCOUNT_NAME                          | Name of the Azure Cosmos DB account, e.g. cosmos-db.                                                               |
| AZURE_DB_DATABASE_NAME                         | Name of the Azure Cosmos DB database to store data, e.g. documents.                                                |
| AZURE_KEY_VAULT_REUSE                          | Whether to reuse an existing Azure Key Vault, e.g. false.                                                          |
| AZURE_KEY_VAULT_RESOURCE_GROUP_NAME            | Name of the Azure Resource Group for the Azure Key Vault to reuse, e.g. key-vault-rg.                              |
| AZURE_KEY_VAULT_NAME                           | Name of the Azure Key Vault, e.g. key-vault.                                                                       |
| AZURE_STORAGE_ACCOUNT_REUSE                    | Whether to reuse an existing Azure Storage account, e.g. false.                                                    |
| AZURE_STORAGE_ACCOUNT_RESOURCE_GROUP_NAME      | Name of the Azure Resource Group for the Azure Storage account to reuse, e.g. storage-account-rg.                  |
| AZURE_STORAGE_ACCOUNT_NAME                     | Name of the Azure Storage account, e.g. storage-account.                                                           |
| AZURE_STORAGE_CONTAINER_NAME                   | Name of the Azure Storage blob container, e.g. documents.                                                          |
| AZURE_VNET_REUSE                               | Whether to reuse an existing Azure Virtual Network, e.g. false.                                                    |
| AZURE_VNET_RESOURCE_GROUP_NAME                 | Name of the Azure Resource Group for the Azure Virtual Network to reuse, e.g. vnet-rg.                             |
| AZURE_VNET_NAME                                | Name of the Azure Virtual Network, e.g. vnet.                                                                      |
| APP_CONFIG_REUSE                               | Whether to reuse an existing Azure App Configuration resource, e.g. false.                                         |
| APP_CONFIG_RESOURCE_GROUP_NAME                 | Name of the Azure Resource Group for the Azure App Configuration resource to reuse, e.g. app-config-rg.            |
| APP_CONFIG_NAME                                | Name of the Azure App Configuration resource, e.g. app-config.                                                     |
| CONTAINER_APPS_ENVIRONMENT_REUSE               | Whether to reuse an existing Azure Container Apps environment, e.g. false.                                         |
| CONTAINER_APPS_ENVIRONMENT_RESOURCE_GROUP_NAME | Name of the Azure Resource Group for the Azure Container Apps environment to reuse, e.g. container-apps-rg.        |
| CONTAINER_APPS_ENVIRONMENT_NAME                | Name of the Azure Container Apps environment, e.g. container-apps-env.                                             |
| AI_HUB_REUSE                                   | Whether to reuse an existing Azure AI Foundry Hub, e.g. false.                                                     |
| AI_HUB_RESOURCE_GROUP_NAME                     | Name of the Azure Resource Group for the Azure AI Foundry Hub to reuse, e.g. ai-hub-rg.                            |
| AI_HUB_NAME                                    | Name of the Azure AI Foundry Hub, e.g. ai-hub.                                                                     |
| AI_HUB_PROJECT_NAME                            | Name of the Azure AI Foundry Project, e.g. ai-project.                                                             |
| AZURE_VPN_DEPLOY_VPN                           | Whether to deploy a VPN Gateway for accessing the Azure resources when using a private virtual network, e.g. true. |
| AZURE_VPN_GATEWAY_NAME                         | Name of the Azure VPN Gateway, e.g. vpn-gateway.                                                                   |
| AZURE_VPN_GATEWAY_PUBLIC_IP_NAME               | Name of the Azure VPN Gateway Public IP, e.g. vpn-gateway-ip.                                                      |
| AZURE_VM_DEPLOY_VM                             | Whether to deploy a VM for accessing the Azure resources when using a private virtual network, e.g. true.          |
| AZURE_VM_NAME                                  | Name of the Azure VM, e.g. vm.                                                                                     |
| AZURE_VM_USER_NAME                             | Name of the Azure VM user, e.g. azureuser.                                                                         |
| AZURE_VM_KV_SEC_NAME                           | Name of the Azure Key Vault secret for the VM password, e.g. vm-password.                                          |
| AZURE_VNET_ADDRESS                             | Address space for the Azure Virtual Network, e.g. 10.0.0.0/23.                                                     |
| AZURE_AI_NSG_NAME                              | Name of the Azure Network Security Group for the AI components, e.g. ai-nsg.                                       |
| AZURE_AI_SUBNET_NAME                           | Name of the Azure Subnet for the AI components, e.g. ai-subnet.                                                    |
| AZURE_AI_SUBNET_PREFIX                         | Address prefix for the Azure Subnet for the AI components, e.g. 10.0.0.0/26.                                       |
| AZURE_ACA_NSG_NAME                             | Name of the Azure Network Security Group for the ACA components, e.g. aca-nsg.                                     |
| AZURE_ACA_SUBNET_NAME                          | Name of the Azure Subnet for the ACA components, e.g. aca-subnet.                                                  |
| AZURE_ACA_SUBNET_PREFIX                        | Address prefix for the Azure Subnet for the ACA components, e.g. 10.0.1.64/26.                                     |
| AZURE_BASTION_NSG_NAME                         | Name of the Azure Network Security Group for the Bastion components, e.g. bastion-nsg.                             |
| AZURE_BASTION_KV_NAME                          | Name of the Azure Key Vault for the Bastion components, e.g. bastion-kv.                                           |
| AZURE_BASTION_SUBNET_PREFIX                    | Address prefix for the Azure Subnet for the Bastion components, e.g. 10.0.0.64/26.                                 |
| AZURE_DATABASE_NSG_NAME                        | Name of the Azure Network Security Group for the Database components, e.g. database-nsg.                           |
| AZURE_DATABASE_SUBNET_NAME                     | Name of the Azure Subnet for the Database components, e.g. database-subnet.                                        |
| AZURE_DATABASE_SUBNET_PREFIX                   | Address prefix for the Azure Subnet for the Database components, e.g. 10.0.1.0/26.                                 |
| AZURE_BLOB_STORAGE_ACCOUNT_PE                  | Name of the Azure Storage Account Blob Private Endpoint, e.g. blob-storage-pe.                                     |
| AZURE_TABLE_STORAGE_ACCOUNT_PE                 | Name of the Azure Storage Account Table Private Endpoint, e.g. table-storage-pe.                                   |
| AZURE_QUEUE_STORAGE_ACCOUNT_PE                 | Name of the Azure Storage Account Queue Private Endpoint, e.g. queue-storage-pe.                                   |
| AZURE_FILE_STORAGE_ACCOUNT_PE                  | Name of the Azure Storage Account File Private Endpoint, e.g. file-storage-pe.                                     |
| AZURE_COSMOS_DB_ACCOUNT_PE                     | Name of the Azure Cosmos DB Account Private Endpoint, e.g. cosmos-db-pe.                                           |
| AZURE_KEY_VAULT_PE                             | Name of the Azure Key Vault Private Endpoint, e.g. key-vault-pe.                                                   |
| AZURE_APP_CONFIG_PE                            | Name of the Azure App Configuration Private Endpoint, e.g. app-config-pe.                                          |
| AZURE_MONITOR_PRIVATE_LINK_NAME                | Name of the Azure Monitor Private Link, e.g. monitor-private-link.                                                 |
| AZURE_LOG_ANALYTICS_PE                         | Name of the Azure Log Analytics Private Endpoint, e.g. log-analytics-pe.                                           |
| AZURE_AI_SERVICES_PE                           | Name of the Azure AI Services Private Endpoint, e.g. ai-services-pe.                                               |
| AZURE_CONTAINER_REGISTRY_PE                    | Name of the Azure Container Registry Private Endpoint, e.g. container-registry-pe.                                 |
| AZURE_CONTAINER_APPS_ENVIRONMENT_PE            | Name of the Azure Container Apps Environment Private Endpoint, e.g. container-apps-env-pe.                         |
| AZURE_AI_HUB_PE                                | Name of the Azure AI Foundry Hub Private Endpoint, e.g. ai-hub-pe.                                                 |
| AZURE_DEPLOY_APP_CONFIG_VALUES                 | Whether to deploy the Azure App Configuration values, e.g. true.                                                   |
| AZURE_OPENAI_API_VERSION                       | The Azure OpenAI API version to use, e.g. 2025-01-01-preview.                                                      |

</details>

### Deploying to Azure

To setup an environment in Azure, you can use the following `azd` commands:

> [!IMPORTANT]
> Review the parameters in the [./infra/core.bicepparam](./infra/core.bicepparam) file, or use the environment variables defined above to customize the deployment to your needs.

```bash
# Login to Azure with Azure Developer CLI (use --tenant-id for specific tenant)
azd auth login

# Build the containerized application and deploy to Azure
azd up
```

<details>
  <summary><strong>Deploy using scripts</strong></summary>

Alternatively to using the `azd` commands, you can use the provided PowerShell or Bash scripts to deploy the infrastructure and application.

```powershell
.\Setup-Environment.ps1 -DeploymentName <DeploymentName> -Location <Location>
```

```bash
bash ./setup_environment.sh <DeploymentName> <Location>
```

</details>

#### Environment Network Isolation

By default, the deployment will be configured to use public endpoints for all Azure resources, secured using Azure Managed Identity and Azure RBAC least privilege access with API key access disabled.

To deploy the environment with network isolation using a virtual network and private endpoints, set the `AZURE_NETWORK_ISOLATION` environment variable to `true` or update the `core.bicepparam` file to set the `networkIsolation` parameter to `true`.

This will deploy additional resources to the environment, including:

- **Virtual Network (VNet)**:
  - Created if `networkIsolation` is `true` (unless reusing an existing VNet).
  - Address space configurable (default: `10.0.0.0/23`).
- **Subnets within the VNet**:
  - AI Services subnet, with private endpoints for:
    - Key Vault
    - App Configuration
    - Storage
    - Cosmos DB
    - AI Foundry
    - AI Services
    - Container Registry
    - Container Apps Environment
  - Azure Container Apps Environment subnet, with delegation for `Microsoft.App/environments`.
  - Bastion subnet, for the Bastion host VM.
- **VPN Gateway** (optional):
  - Deployed if `deployVPN` is `true` and `networkIsolation` is enabled.
- **Bastion Host VM** (optional):
  - Deployed if `deployVM` is `true` and `networkIsolation` is enabled.
  - Includes Microsoft Entra ID authentication extension.

### Running the application locally

For local development and testing in the devcontainer, you can run the application locally with `F5` debugging in Visual Studio Code.

> [!NOTE]
> If you require local Azure Storage emulation, you can run `docker-compose up` to start a local Azurite instance.

### Testing the pre-built pipeline

Once an environment is setup, you can run the pre-built pipeline by uploading a batch of documents to the Azure Storage blob container and sending a message via a HTTP request or Azure Storage queue containing the container reference.

A batch of invoices is provided in the tests [Invoice Batch folder](./tests/InvoiceBatch/) which can be uploaded into an Azure Storage blob container, locally via Azurite, or in the deployed Azure Storage account.

These files can be uploaded using the Azure VS Code extension or the Azure Storage Explorer.

![Azurite Local Blob Storage Upload](./assets/Local-Blob-Upload.png)

> [!NOTE]
> Upload all of the individual folders into the container, not the individual files. This sample processed a container that contains multiple folders, each representing a customer's data to be processed which may contain one or more invoices.

#### Via the HTTP trigger

To send via HTTP, open the [`tests/HttpTrigger.rest`](./tests/HttpTrigger.rest) file and use the request to trigger the pipeline.

```http
POST http://localhost:7071/api/process-documents
Content-Type: application/json

{
    "container_name": "documents"
}
```

To run in Azure, replace `http://localhost:7071` with the `environmentInfo.value.applicationContainerAppUrl` value from the [`./infra/scripts/InfrastructureOutputs.json`](./infra/scripts/InfrastructureOutputs.json) file after deployment.

#### Via the Azure Storage queue

To send via the Azure Storage queue, run the [`tests/QueueTrigger.ps1`](./tests/QueueTrigger.ps1) PowerShell script to trigger the pipeline.

This will add the following message to the **documents** queue in the Azure Storage account, Base64 encoded:

```json
{
  "container_name": "documents"
}
```

To run in Azure, replace the `az storage message put` command with the following:

```powershell
az storage message put `
    --content $Base64EncodedMessage `
    --queue-name "documents" `
    --account-name "<storage-account-name>" `
    --auth-mode login `
    --time-to-live 86400
```

The `--account-name` parameter should be replaced with the name of the Azure Storage account deployed in the environment found in the `environmentInfo.value.azureStorageAccount` value from the [`./infra/InfrastructureOutputs.json`](./infra/InfrastructureOutputs.json) file after deployment.

## FAQ

### How are confidence scores calculated?

For Azure OpenAI, confidence scores can be calculated by first enabling the `logprobs` feature in the model request. This will return the log probabilities of the tokens generated by the model, which can be used to calculate a confidence score for structured outputs of the model by comparing the key-value pairs to their generated tokens log probabilities.

> [!NOTE]
> See the [`openai_confidence`](./src/AIDocumentPipeline/shared/confidence/openai_confidence.py) module for the implementation of calculating the confidence score for the Azure OpenAI model using a structured output.

> [!IMPORTANT]
> Do not use prompting to generate confidence scores as part of the generated output, as this will not be a reliable source of truth. The `logprobs` feature is the only reliable technique, using the model's internal mechanisms for evaluating the probability of the tokens that it generates.

For Azure AI Document Intelligence, confidence scores are automatically calculated and returned by models for the words detected in the document. These scores can be combined with the Azure OpenAI model confidence scores to calculate an overall confidence score when combining the two techniques for higher accuracy extractions.

> [!NOTE]
> See the [`document_intelligence_confidence`](./src/AIDocumentPipeline/shared/confidence/document_intelligence_confidence.py) module for the implementation of calculating the confidence score for the Azure AI Document Intelligence model using a structured output.

### I deployed with network isolation, how can I access the resources?

When deploying with network isolation, you can access the Azure resources using either the deployed VPN Gateway or Bastion host. The VPN Gateway allows you to connect to the Azure resources using a VPN client, while the Bastion host allows you to connect to a jumpbox VM in the Azure environment using the Azure portal.

> [!NOTE]
> If you are using the jumpbox VM, you can use the [./infra/scripts/Initialize-VM.ps1](./infra/scripts/Initialize-VM.ps1) script to install the necessary tools and dependencies on the VM to build and deploy the application.

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
