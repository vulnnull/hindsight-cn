# RetainResponse

Response model for retain endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**bank_id** | **str** |  | 
**items_count** | **int** |  | 
**var_async** | **bool** | Whether the operation was processed asynchronously | 

## Example

```python
from hindsight_client_api.models.retain_response import RetainResponse

# TODO update the JSON string below
json = "{}"
# create an instance of RetainResponse from a JSON string
retain_response_instance = RetainResponse.from_json(json)
# print the JSON string representation of the object
print(RetainResponse.to_json())

# convert the object into a dict
retain_response_dict = retain_response_instance.to_dict()
# create an instance of RetainResponse from a dict
retain_response_from_dict = RetainResponse.from_dict(retain_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


