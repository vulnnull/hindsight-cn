# BankListResponse

Response model for listing all banks.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**banks** | [**List[BankListItem]**](BankListItem.md) |  | 

## Example

```python
from hindsight_client_api.models.bank_list_response import BankListResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BankListResponse from a JSON string
bank_list_response_instance = BankListResponse.from_json(json)
# print the JSON string representation of the object
print(BankListResponse.to_json())

# convert the object into a dict
bank_list_response_dict = bank_list_response_instance.to_dict()
# create an instance of BankListResponse from a dict
bank_list_response_from_dict = BankListResponse.from_dict(bank_list_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


