# CancelOperationResponse

Response model for cancel operation endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**message** | **str** |  | 
**operation_id** | **str** |  | 

## Example

```python
from hindsight_client_api.models.cancel_operation_response import CancelOperationResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CancelOperationResponse from a JSON string
cancel_operation_response_instance = CancelOperationResponse.from_json(json)
# print the JSON string representation of the object
print(CancelOperationResponse.to_json())

# convert the object into a dict
cancel_operation_response_dict = cancel_operation_response_instance.to_dict()
# create an instance of CancelOperationResponse from a dict
cancel_operation_response_from_dict = CancelOperationResponse.from_dict(cancel_operation_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


