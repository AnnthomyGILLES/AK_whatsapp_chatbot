import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def count_tokens(phrase):
    n = encoding.encode(phrase)
    return len(n)
