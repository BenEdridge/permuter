#!/usr/bin/env python

# Inspired by:
# https://github.com/RhinoSecurityLabs/GCPBucketBrute
# https://github.com/koenrh/s3enum

import sys
import socket
import requests
import re
from itertools import permutations

def is_valid_bucket_name(bucket_name):
    # Check length
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        return False

    # Check format
    if not re.match(r'^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$', bucket_name):
        return False

    # Check adjacent periods
    if '..' in bucket_name:
        return False

    # Check IP address format
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', bucket_name):
        return False

    # Check prefix xn--
    if bucket_name.startswith('xn--'):
        return False

    # Check suffix -s3alias
    if bucket_name.endswith('-s3alias'):
        return False

    # Check suffix --ol-s3
    if bucket_name.endswith('--ol-s3'):
        return False

    return True

def generate_permutations(wordlists):
    all_words = []
    for wordlist in wordlists:
        with open(wordlist, 'r', encoding='utf-8') as file:
            words = [line.strip() for line in file]
            # filter out empty lines
            words = list(filter(None, words))
            
            # remove duplicates
            words = list(dict.fromkeys(words))
            
            # convert to lowercase
            words = [word.lower() for word in words]
            all_words.extend(words)

    for name in permutations(all_words, 2):
        generated_permutation = ''.join(name)
        if is_valid_bucket_name(generated_permutation):
            yield generated_permutation

def print_usage():
    print("Usage: permutation.py [WORDLISTS]...")
    print("Generates permutations from wordlists and performs DNS lookups for valid bucket names.")
    print("\nArguments:")
    print("  WORDLISTS    Path(s) to the wordlist file(s).")
    print("\nExample:")
    print("  permutation.py wordlist1.txt wordlist2.txt")

def print_help():
    print("Permutation Generator and DNS Lookup Script")
    print("\nDescription:")
    print("This script takes wordlists as input and generates permutations from the words.")
    print("It then performs DNS lookups for the generated permutations that comply with the S3 bucket name rules.")
    print("\nUsage:")
    print_usage()

if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
    print_help()
    sys.exit()

wordlists_from_args = sys.argv[1:]

# Generate permutations
result = generate_permutations(wordlists_from_args)

for permutation in result:
    # AWS doesn't support _ in bucket names
    if '_' not in permutation:
        domain = f'{permutation}.s3.amazonaws.com'
        try:
            # Perform DNS lookups for Amazon S3
            ip_address = socket.gethostbyname(domain)
            cname = socket.gethostbyaddr(ip_address)[0]
            if cname == "s3-1-w.amazonaws.com":
                # print(f"Bucket does not exist: {domain}")
                continue
            else:
                print(f'https://{domain}')
        except socket.error as e:
            print(f'DNS lookup failed: {domain}, Error: {e}')


    # Perform HTTP requests for Google Cloud Storage
    url = f'https://storage.googleapis.com/{permutation}'
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            continue
        print(f'{response.status_code} {url}')
    except requests.exceptions.RequestException as e:
        print(f'Request failed: {url}, Error: {e}')
