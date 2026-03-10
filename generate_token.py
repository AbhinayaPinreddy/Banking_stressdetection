from livekit import api

api_key = "devkey"
api_secret = "secretsecretsecretsecretsecretsecret"

token = (
    api.AccessToken(api_key, api_secret)
    .with_identity("user1")
    .with_name("User 1")
    .with_grants(api.VideoGrants(
        room_join=True,
        room="test-room"
    ))
)

print(token.to_jwt())