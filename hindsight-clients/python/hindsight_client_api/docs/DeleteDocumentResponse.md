# DeleteDocumentResponse

Response model for delete document endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**message** | **str** |  | 
**document_id** | **str** |  | 
**memory_units_deleted** | **int** |  | 

## Example

```python
from hindsight_client_api.models.delete_document_response import DeleteDocumentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteDocumentResponse from a JSON string
delete_document_response_instance = DeleteDocumentResponse.from_json(json)
# print the JSON string representation of the object
print(DeleteDocumentResponse.to_json())

# convert the object into a dict
delete_document_response_dict = delete_document_response_instance.to_dict()
# create an instance of DeleteDocumentResponse from a dict
delete_document_response_from_dict = DeleteDocumentResponse.from_dict(delete_document_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


