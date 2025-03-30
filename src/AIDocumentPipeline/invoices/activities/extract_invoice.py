"""Extracts invoice data from a document.

This module provides the blueprint for an Azure Function activity that extracts invoice data from a document using Azure OpenAI.
"""

from __future__ import annotations
from pydantic import Field
from documents.services.document_data_extractor import DocumentDataExtractor, DocumentDataExtractorOptions
from invoices.models.invoice import Invoice
from shared.workflows.base_request import BaseRequest
from shared.workflows.validation_result import ValidationResult
from storage.services.azure_storage_client_factory import AzureStorageClientFactory
import shared.identity as identity
from shared import app_settings
import azure.durable_functions as df
import logging
from typing import Optional

name = "ExtractInvoice"
bp = df.Blueprint()
storage_factory = AzureStorageClientFactory(identity.default_credential)
document_extractor = DocumentDataExtractor(identity.default_credential)


@bp.function_name(name)
@bp.activity_trigger(input_name="input", activity=name)
def run(input: Request) -> Optional[Invoice]:
    """Extracts invoice data from a document using Azure OpenAI.

    :param input: The request containing the container name and blob name of the document.
    :return: The extracted invoice data if successful; otherwise, None.
    """

    validation_result = input.validate()
    if not validation_result.is_valid:
        logging.error(f"Invalid input: {validation_result.to_str()}")
        return None

    blob_content = storage_factory.get_blob_content(
        app_settings.azure_storage_account, input.container_name, input.blob_name)

    data = document_extractor.from_bytes(
        blob_content,
        Invoice,
        DocumentDataExtractorOptions(
            extraction_prompt="""Extract the data from this invoice.
    - If a value is not present, provide null.
    - It is possible that there are multiple invoices in the same document across multiple pages.
    - Some values must be inferred based on the content defined in the invoice.
    - Dates should be in the format YYYY-MM-DD.""",
            page_start=input.page_range_start,
            page_end=input.page_range_end,
            aiservices_endpoint=app_settings.azure_aiservices_endpoint,
            openai_endpoint=app_settings.azure_openai_endpoint,
            deployment_name=app_settings.azure_openai_chat_deployment,
            max_tokens=4096,
            temperature=0.1,
            top_p=0.1
        ))

    return data


class Request(BaseRequest):
    """Defines the request payload for the `ExtractInvoice` activity."""

    container_name: str = Field(
        description="The name of the container within the storage account.")
    blob_name: str = Field(
        description="The name of the document blob to extract data from.")
    page_range_start: Optional[int] = Field(
        default=None, description="The starting page number of the document to extract data from.")
    page_range_end: Optional[int] = Field(
        default=None, description="The ending page number of the document to extract data from.")

    def validate(self) -> ValidationResult:
        result = ValidationResult()

        if not self.container_name:
            result.add_error("container_name is required")

        if not self.blob_name:
            result.add_error("blob_name is required")

        if self.page_range_start is not None and self.page_range_end is not None:
            if self.page_range_start < 1 or self.page_range_end < 1:
                result.add_error(
                    "page_range_start and page_range_end must be greater than 0")
            if self.page_range_start > self.page_range_end:
                result.add_error(
                    "page_range_start must be less than or equal to page_range_end")

        return result

    @staticmethod
    def to_json(obj: Request) -> str:
        """
        Convert the Request object to a JSON string.

        For more information on this serialization method for Azure Functions, see:
        https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-serialization-and-persistence?tabs=python
        """
        return obj.model_dump_json()

    @staticmethod
    def from_json(json_str: str) -> Request:
        """
        Convert a JSON string to an Request object.

        For more information on this serialization method for Azure Functions, see:
        https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-serialization-and-persistence?tabs=python
        """
        return Request.model_validate_json(json_str)
