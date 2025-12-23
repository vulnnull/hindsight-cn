# OperationResponse

Response model for a single async operation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**task_type** | **str** |  | 
**items_count** | **int** |  | 
**document_id** | **str** |  | 
**created_at** | **str** |  | 
**status** | **str** |  | 
**error_message** | **str** |  | 

## Example

```python
from hindsight_client_api.models.operation_response import OperationResponse

# TODO update the JSON string below
json = "{}"
# create an instance of OperationResponse from a JSON string
operation_response_instance = OperationResponse.from_json(json)
# print the JSON string representation of the object
print(OperationResponse.to_json())

# convert the object into a dict
operation_response_dict = operation_response_instance.to_dict()
# create an instance of OperationResponse from a dict
operation_response_from_dict = OperationResponse.from_dict(operation_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


