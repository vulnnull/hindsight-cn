# UpdateDispositionRequest

Request model for updating disposition traits.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**disposition** | [**DispositionTraits**](DispositionTraits.md) |  | 

## Example

```python
from hindsight_client_api.models.update_disposition_request import UpdateDispositionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateDispositionRequest from a JSON string
update_disposition_request_instance = UpdateDispositionRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateDispositionRequest.to_json())

# convert the object into a dict
update_disposition_request_dict = update_disposition_request_instance.to_dict()
# create an instance of UpdateDispositionRequest from a dict
update_disposition_request_from_dict = UpdateDispositionRequest.from_dict(update_disposition_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


