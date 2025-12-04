# BackgroundResponse

Response model for background update.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**background** | **str** |  | 
**disposition** | [**DispositionTraits**](DispositionTraits.md) |  | [optional] 

## Example

```python
from hindsight_client_api.models.background_response import BackgroundResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BackgroundResponse from a JSON string
background_response_instance = BackgroundResponse.from_json(json)
# print the JSON string representation of the object
print(BackgroundResponse.to_json())

# convert the object into a dict
background_response_dict = background_response_instance.to_dict()
# create an instance of BackgroundResponse from a dict
background_response_from_dict = BackgroundResponse.from_dict(background_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


