import requests
import pprint

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

def _execute_gql_query(query: str, variables: dict) -> dict: 
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
    
def get_schools_data(query: str) -> list[dict]:
    """ Get the data for the schools that match the query. """
    data = _execute_gql_query(SCHOOL_SEARCH_QUERY, {"text": query})
    return data["newSearch"]["schools"]["edges"]

def get_professors_data(query: str, school_id: str) -> list[dict]:
    """ Get the data for the professors that match the query and school id. """
    data = _execute_gql_query(PROFESSOR_SEARCH_QUERY, {"text": query, "sid": school_id})
    return data["newSearch"]["teachers"]["edges"]

if __name__ == "__main__":
    schools = get_schools_data("College Station")
    pprint.pprint(schools)
    
    professors = get_professors_data("Amy Austin", schools[0]['node']['id'])
    pprint.pprint(professors)