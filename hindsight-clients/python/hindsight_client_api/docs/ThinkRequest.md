# ThinkRequest

Request model for think endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** |  | 
**thinking_budget** | **int** |  | [optional] [default to 50]
**context** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.think_request import ThinkRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ThinkRequest from a JSON string
think_request_instance = ThinkRequest.from_json(json)
# print the JSON string representation of the object
print(ThinkRequest.to_json())

# convert the object into a dict
think_request_dict = think_request_instance.to_dict()
# create an instance of ThinkRequest from a dict
think_request_from_dict = ThinkRequest.from_dict(think_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


