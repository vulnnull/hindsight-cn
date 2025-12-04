# CreateBankRequest

Request model for creating/updating a bank.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**disposition** | [**DispositionTraits**](DispositionTraits.md) |  | [optional] 
**background** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.create_bank_request import CreateBankRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateBankRequest from a JSON string
create_bank_request_instance = CreateBankRequest.from_json(json)
# print the JSON string representation of the object
print(CreateBankRequest.to_json())

# convert the object into a dict
create_bank_request_dict = create_bank_request_instance.to_dict()
# create an instance of CreateBankRequest from a dict
create_bank_request_from_dict = CreateBankRequest.from_dict(create_bank_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


