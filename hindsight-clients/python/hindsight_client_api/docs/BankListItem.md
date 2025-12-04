# BankListItem

Bank list item with profile summary.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bank_id** | **str** |  | 
**name** | **str** |  | 
**disposition** | [**DispositionTraits**](DispositionTraits.md) |  | 
**background** | **str** |  | 
**created_at** | **str** |  | [optional] 
**updated_at** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.bank_list_item import BankListItem

# TODO update the JSON string below
json = "{}"
# create an instance of BankListItem from a JSON string
bank_list_item_instance = BankListItem.from_json(json)
# print the JSON string representation of the object
print(BankListItem.to_json())

# convert the object into a dict
bank_list_item_dict = bank_list_item_instance.to_dict()
# create an instance of BankListItem from a dict
bank_list_item_from_dict = BankListItem.from_dict(bank_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


