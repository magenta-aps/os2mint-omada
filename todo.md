skriv test: synkroniser adresser/it-user til eksisterende sd-bruger

slet omada-engagement automatisk eller engangsoprydning?

```graphql
query MyQuery {
  employees(filter: { uuids: "a63019f4-0b46-44eb-8c4f-9622a954f9d2" }) {
    objects {
      current {
        engagements {
          user_key
          engagement_type {
            user_key
          }
        }
        addresses {
          address_type {
            user_key
          }
          engagement {
            user_key
          }
          ituser {
            user_key
          }
        }
        itusers {
          user_key
          engagements {
            current {
              user_key
            }
          }
        }
      }
    }
  }
}
```

```json
{
  "data": {
    "employees": {
      "objects": [
        {
          "current": {
            "engagements": [
              {
                "user_key": "1000F",
                "engagement_type": {
                  "user_key": "omada_manually_created_hidden"
                }
              },
              {
                "user_key": "SJ-31876",
                "engagement_type": {
                  "user_key": "deltid"
                }
              },
              {
                "user_key": "TF-10005",
                "engagement_type": {
                  "user_key": "deltid"
                }
              }
            ],
            "addresses": [
              {
                "address_type": {
                  "user_key": "EmailEmployee"
                },
                "engagement": [
                  {
                    "user_key": "1000F"
                  }
                ],
                "ituser": [
                  {
                    "user_key": "DR1000FZ"
                  }
                ]
              },
              {
                "address_type": {
                  "user_key": "MobilePhoneEmployee"
                },
                "engagement": [
                  {
                    "user_key": "1000F"
                  }
                ],
                "ituser": [
                  {
                    "user_key": "DR1000FZ"
                  }
                ]
              },
              {
                "address_type": {
                  "user_key": "PhoneEmployee"
                },
                "engagement": [
                  {
                    "user_key": "1000F"
                  }
                ],
                "ituser": [
                  {
                    "user_key": "DR1000FZ"
                  }
                ]
              }
            ],
            "itusers": [
              {
                "user_key": "DR1000FZ",
                "engagements": [
                  {
                    "current": {
                      "user_key": "1000F"
                    }
                  }
                ]
              },
              {
                "user_key": "df19c237-e7e4-4d32-a3a4-b82a24651dac",
                "engagements": [
                  {
                    "current": {
                      "user_key": "1000F"
                    }
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  }
}
```
