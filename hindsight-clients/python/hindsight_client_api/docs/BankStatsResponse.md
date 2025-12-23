# BankStatsResponse

Response model for bank statistics endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bank_id** | **str** |  | 
**total_nodes** | **int** |  | 
**total_links** | **int** |  | 
**total_documents** | **int** |  | 
**nodes_by_fact_type** | **Dict[str, int]** |  | 
**links_by_link_type** | **Dict[str, int]** |  | 
**links_by_fact_type** | **Dict[str, int]** |  | 
**links_breakdown** | **Dict[str, Dict[str, int]]** |  | 
**pending_operations** | **int** |  | 
**failed_operations** | **int** |  | 

## Example

```python
from hindsight_client_api.models.bank_stats_response import BankStatsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BankStatsResponse from a JSON string
bank_stats_response_instance = BankStatsResponse.from_json(json)
# print the JSON string representation of the object
print(BankStatsResponse.to_json())

# convert the object into a dict
bank_stats_response_dict = bank_stats_response_instance.to_dict()
# create an instance of BankStatsResponse from a dict
bank_stats_response_from_dict = BankStatsResponse.from_dict(bank_stats_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


