import requests

API_URL = "https://www.ratemyprofessors.com/graphql"
API_HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",          # mandatory Basic-auth
    "Content-Type":  "application/json",
    "Origin":        "https://www.ratemyprofessors.com",
    "Referer":       "https://www.ratemyprofessors.com/",
    "User-Agent":    "Mozilla/5.0 (simple-RMP-CLI)",
}

SCHOOL_SEARCH_QUERY = """
query ($text: String!) {
  newSearch {
    schools(query: { text: $text }) {
      edges { node { id name city state } }
    }
  }
}
"""

PROFESSOR_SEARCH_QUERY = """
query ($text: String!, $sid: ID!) {
  newSearch {
    teachers(query: { text: $text, schoolID: $sid }) {
      edges {
        node {
          firstName
          lastName
          legacyId
          department
          avgRating
          avgDifficulty
          numRatings
          wouldTakeAgainPercent
        }
      }
    }
  }
}
"""

def execute_gql_query(query: str, variables: dict) -> dict: 
    """ Execute a GraphQL query and return the response data. """
    try:
        response = requests.post(API_URL, headers=API_HEADERS, json={"query": query, "variables": variables}, timeout=15)
        
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get("errors"):
            raise RuntimeError(response_data["errors"])
    
        return response_data["data"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to execute GraphQL query: {e}")
    
