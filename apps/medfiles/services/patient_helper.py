import time
import json
import requests
from azure.identity import ClientSecretCredential

# Microsoft Entra (Azure AD) credentials
tenant_id = 
client_id =   
client_secret = 
scope = 

# Microsoft Fabric GraphQL API endpoint
graphql_api_url = "https://27123242df7241f7822b0b14db152c20.z27.graphql.fabric.microsoft.com/v1/workspaces/27123242-df72-41f7-822b-0b14db152c20/graphqlapis/83b6e009-3d9d-4f09-a547-c52dc56c8c57/graphql"

def normalize_name(name: str) -> str:
    if not name:
        return name
    return ' '.join(word.capitalize() for word in name.split())

def build_filter(filter_fields):
    conditions = []

    # Handle name search
    first = filter_fields.get("first_name")
    last = filter_fields.get("last_name")

    if first and last:
        conditions.append({
            "or": [
                {
                    "and": [
                        {"PAPMI_Name2": {"contains": first}},
                        {"PAPMI_Name": {"contains": last}}
                    ]
                },
                {
                    "and": [
                        {"PAPMI_Name": {"contains": first}},
                        {"PAPMI_Name2": {"contains": last}}
                    ]
                }
            ]
        })
    elif first:
        conditions.append({"PAPMI_Name2": {"contains": first}})
    elif last:
        conditions.append({"PAPMI_Name": {"contains": last}})

    # Other filters
    if filter_fields.get("PAPMI_DOB"):
        conditions.append({"PAPMI_DOB": {"eq": filter_fields["PAPMI_DOB"]}})
    if filter_fields.get("PAPMI_MobPhone"):
        conditions.append({"PAPMI_MobPhone": {"eq": filter_fields["PAPMI_MobPhone"]}})
    if filter_fields.get("PAPMI_ID"):
        conditions.append({"PAPMI_ID": {"eq": filter_fields["PAPMI_ID"]}})

    if len(conditions) == 1:
        return conditions[0]
    elif conditions:
        return {"and": conditions}
    else:
        return {}

def dict_to_graphql(obj):
    if isinstance(obj, dict):
        fields = []
        for k, v in obj.items():
            fields.append(f"{k}: {dict_to_graphql(v)}")
        return "{ " + ", ".join(fields) + " }"
    elif isinstance(obj, list):
        return "[ " + ", ".join(dict_to_graphql(v) for v in obj) + " ]"
    elif isinstance(obj, str):
        return f"\"{obj}\""
    else:
        return str(obj)

def get_access_token():
    try:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        token = credential.get_token(*scope)
        return token.token
    except Exception as e:
        print(f"❌ Error: Could not get access token: {str(e)}")
        raise

def call_graphql_api_with_retry(access_token, query, retries=5, backoff_factor=1):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries):
        try:
            response = requests.post(graphql_api_url, headers=headers, json={'query': query})
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                wait = backoff_factor * (2 ** attempt) + retry_after
                print(f"⚠️ Rate limited (429). Waiting {wait} seconds before retrying... (Attempt {attempt + 1})")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed on attempt {attempt + 1}: {str(e)}")
            if attempt == retries - 1:
                raise Exception(f"Exceeded maximum retries: {str(e)}")
            time.sleep(backoff_factor * (2 ** attempt))

def getpatid(filter_fields):
    try:
        # Normalize names
        if filter_fields.get("first_name"):
            filter_fields["first_name"] = normalize_name(filter_fields["first_name"])
        if filter_fields.get("last_name"):
            filter_fields["last_name"] = normalize_name(filter_fields["last_name"])

        # Acquire token
        access_token = get_access_token()
        print("✅ Access token retrieved successfully")

        # Build filter
        filter_json = build_filter(filter_fields)
        filter_str = dict_to_graphql(filter_json) if filter_json else "{}"

        # Fields to fetch
        item_fields = [
            "PAPMI_DOB",
            "PAPMI_MobPhone",
            "PAPMI_No",
            "PAPMI_Name",
            "PAPMI_ID",
            "PAPMI_Name2"
        ]
        items_str = "\n          ".join(item_fields)

        # Build query
        query = f"""
        query {{
          pA_PatMas(
            filter: {filter_str}
            first: 10000
          ) {{
            items {{
              {items_str}
            }}
          }}
        }}
        """

        print("\n🔍 Generated GraphQL Query:\n", query)

        # Execute query with retry logic
        data = call_graphql_api_with_retry(access_token, query)
        # print("🔍 Parsed JSON Response:\n", json.dumps(data, indent=2))

        if "errors" in data:
            print("❌ GraphQL Errors:", json.dumps(data["errors"], indent=2))
            return "GraphQL internal error"

        items = data.get('data', {}).get('pA_PatMas', {}).get('items', [])
        if not items:
            print("⚠️ No matching patient found")
            return []

        # Add full_name field
        for item in items:
            item['full_name'] = f"{item.get('PAPMI_Name', '')} {item.get('PAPMI_Name2', '')}".strip()

        return items

    except Exception as error:
        print(f"❌ Query failed with error: {error}")
        return []