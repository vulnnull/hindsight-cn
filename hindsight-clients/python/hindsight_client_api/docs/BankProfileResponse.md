# BankProfileResponse

Response model for bank profile.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bank_id** | **str** |  | 
**name** | **str** |  | 
**disposition** | [**DispositionTraits**](DispositionTraits.md) |  | 
**background** | **str** |  | 

## Example

```python
from hindsight_client_api.models.bank_profile_response import BankProfileResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BankProfileResponse from a JSON string
bank_profile_response_instance = BankProfileResponse.from_json(json)
# print the JSON string representation of the object
print(BankProfileResponse.to_json())

# convert the object into a dict
bank_profile_response_dict = bank_profile_response_instance.to_dict()
# create an instance of BankProfileResponse from a dict
bank_profile_response_from_dict = BankProfileResponse.from_dict(bank_profile_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


