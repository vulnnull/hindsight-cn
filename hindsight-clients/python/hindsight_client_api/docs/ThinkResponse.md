# ThinkResponse

Response model for think endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | 
**based_on** | [**List[ThinkFact]**](ThinkFact.md) |  | [optional] [default to []]
**new_opinions** | **List[str]** |  | [optional] [default to []]

## Example

```python
from hindsight_client_api.models.think_response import ThinkResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ThinkResponse from a JSON string
think_response_instance = ThinkResponse.from_json(json)
# print the JSON string representation of the object
print(ThinkResponse.to_json())

# convert the object into a dict
think_response_dict = think_response_instance.to_dict()
# create an instance of ThinkResponse from a dict
think_response_from_dict = ThinkResponse.from_dict(think_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


