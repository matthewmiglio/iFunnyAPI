import random

community_bearer_tokens_list_fp = r"community_bearer_tokens.txt"


def get_random_community_bearer_token():
    with open(community_bearer_tokens_list_fp, "r") as f:
        community_bearer_tokens_list = f.read().splitlines()
        community_bearer_tokens_list = [
            l.replace("\n", "") for l in community_bearer_tokens_list if l != ""
        ]

    random_token = random.choice(community_bearer_tokens_list)
    return random_token


if __name__ == "__main__":
    this_random_token = get_random_community_bearer_token()
    print(f'Retrieved this random token "{this_random_token}"')
