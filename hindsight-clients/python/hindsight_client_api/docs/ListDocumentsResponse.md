# ListDocumentsResponse

Response model for list documents endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | **List[Dict[str, object]]** |  | 
**total** | **int** |  | 
**limit** | **int** |  | 
**offset** | **int** |  | 

## Example

```python
from hindsight_client_api.models.list_documents_response import ListDocumentsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ListDocumentsResponse from a JSON string
list_documents_response_instance = ListDocumentsResponse.from_json(json)
# print the JSON string representation of the object
print(ListDocumentsResponse.to_json())

# convert the object into a dict
list_documents_response_dict = list_documents_response_instance.to_dict()
# create an instance of ListDocumentsResponse from a dict
list_documents_response_from_dict = ListDocumentsResponse.from_dict(list_documents_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


