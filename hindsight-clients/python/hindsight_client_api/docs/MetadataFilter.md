# MetadataFilter

Filter for metadata fields. Matches records where (key=value) OR (key not set) when match_unset=True.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** | Metadata key to filter on | 
**value** | **str** |  | [optional] 
**match_unset** | **bool** | If True, also match records where this metadata key is not set | [optional] [default to True]

## Example

```python
from hindsight_client_api.models.metadata_filter import MetadataFilter

# TODO update the JSON string below
json = "{}"
# create an instance of MetadataFilter from a JSON string
metadata_filter_instance = MetadataFilter.from_json(json)
# print the JSON string representation of the object
print(MetadataFilter.to_json())

# convert the object into a dict
metadata_filter_dict = metadata_filter_instance.to_dict()
# create an instance of MetadataFilter from a dict
metadata_filter_from_dict = MetadataFilter.from_dict(metadata_filter_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


