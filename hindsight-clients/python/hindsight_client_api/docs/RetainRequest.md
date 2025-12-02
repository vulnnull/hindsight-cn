# RetainRequest

Request model for retain endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[MemoryItem]**](MemoryItem.md) |  | 
**var_async** | **bool** | If true, process asynchronously in background. If false, wait for completion (default: false) | [optional] [default to False]

## Example

```python
from hindsight_client_api.models.retain_request import RetainRequest

# TODO update the JSON string below
json = "{}"
# create an instance of RetainRequest from a JSON string
retain_request_instance = RetainRequest.from_json(json)
# print the JSON string representation of the object
print(RetainRequest.to_json())

# convert the object into a dict
retain_request_dict = retain_request_instance.to_dict()
# create an instance of RetainRequest from a dict
retain_request_from_dict = RetainRequest.from_dict(retain_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


