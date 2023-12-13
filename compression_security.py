import argparse
import os
import sys
import numpy
import time
import random
import string
import csv
import itertools
import math
import requests
from bs4 import BeautifulSoup

# Append scl to path in order to import encoders and decoders
sys.path.append('../stanford_compression_library')
from scl.compressors.lz77 import LZ77Encoder, LZ77Decoder
from scl.compressors.lz77_sliding_window import LZ77SlidingWindowEncoder, HashBasedMatchFinder
from scl.core.data_block import DataBlock


def fetch_sherlock_holmes_novel():
    url = "https://www.gutenberg.org/ebooks/1661.txt.utf-8"  # Sherlock Holmes novel on Project Gutenberg
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch the novel. Status Code: {response.status_code}")
        return None


def clean_text(raw_text):
    # You may need to customize this function based on the specific format of the novel text
    # This example removes Project Gutenberg's metadata at the beginning and end of the novel
    start_marker = "I. A SCANDAL IN BOHEMIA"
    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK THE ADVENTURES OF SHERLOCK HOLMES ***"
    start_index = raw_text.find(start_marker) + len(start_marker)
    end_index = raw_text.find(end_marker)
    raw_text = raw_text[start_index:end_index]
    raw_text = ''.join(i for i in raw_text if ord(i)<128)
    raw_text = raw_text.replace("\n", " ").replace("\r", "")
    return raw_text.strip()


def get_random_string(length, letters=None):
    # Generate key of all lowercase letters
    if letters == None:
        letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def generate_text_with_secret_key(text, L, secret_key, prefix):
    # Get random index to pull text from novel and get random index to insert secret
    start_index = random.randint(0, len(text) - L)
    secret_index = random.randint(0, L)
    text = text[start_index:start_index+L]
 
    # Embed the secret key within the text
    key_with_prefix = prefix + secret_key
    text_with_key = text[:secret_index] + key_with_prefix + text[secret_index+1:]
    binary_text = text_with_key.encode('utf-8')
    return binary_text


def run_trials_compute_compression_metrics(iterations, text, letters, prefix, L):
    # Loop through iterations and collect statistics
    compression_stats = []
    for t in range(iterations):
        print(f"running trial {t}")

        # Generate secret
        secret = get_random_string(32, letters)
        
        # Get text
        text_with_key = generate_text_with_secret_key(sherlock_novel_cleaned, L, secret, prefix)
        uncompressed_size = len(text_with_key)*8
        print(text_with_key)
        print(uncompressed_size)

        for i in range(len(secret)):
            # LZ77 initialization
            seed = prefix + secret[:i]
            seed_bin = seed.encode('utf-8')
            encoder = LZ77Encoder(initial_window=seed_bin)
            decoder = LZ77Decoder(initial_window=seed_bin)
            num_char_of_secret_key = i

            # Encode text
            start = time.time()
            encoded_text = encoder.encode_block(DataBlock(list(text_with_key)))
            end = time.time()
            comp_time = end - start

            # Decode text
            start = time.time()
            decoded_text = decoder.decode_block(encoded_text)
            end = time.time()
            decomp_time = end - start

            # Compute ratio
            compressed_size = len(encoded_text)
            print(compressed_size)
            compression_ratio = float(compressed_size)/float(uncompressed_size)

            # Append stats
            compression_stats.append([num_char_of_secret_key, comp_time, decomp_time, compression_ratio])

    # Initialize csv file
    csv_fields = ['num secret char in seed', 'compression time', 'decompression time', 'compression ratio']
    csv_filename = "compression_stats.csv"
    # writing to csv file 
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
    with open(csv_filename, 'w') as csvfile:  
        csvwriter = csv.writer(csvfile)              
        csvwriter.writerow(csv_fields)
        csvwriter.writerows(compression_stats) 
    return


def get_lz77_compression_ratio_for_substrings_of_key(text_with_key, secret, prefix, letters):
    # Get compression ratio for the seed=prefix
    seed_base = prefix
    encoder_no_seed = LZ77Encoder(initial_window=seed_base.encode('utf-8'))
    encoded_text = encoder_no_seed.encode_block(DataBlock(list(text_with_key)))
    uncompressed_size = len(text_with_key)*8
    compressed_size_base_seed = len(encoded_text)
    compression_ratio_base_seed = float(compressed_size_base_seed)/float(uncompressed_size)
    print(f"compression rate with seed=prefix: {compression_ratio_base_seed}\n")

    # Keep track of num characters needed to improve ratio
    increments_required_for_lower_compression_ratio = []

    # Add a single character to the seed to see how the compression ratio changes
    compression_ratio_new = compression_ratio_base_seed
    for i in range(len(secret)):
        seed = seed_base + secret[:i] 
        seed_bin = seed.encode('utf-8')
        encoder = LZ77Encoder(initial_window=seed_bin)
        encoded_text = encoder.encode_block(DataBlock(list(text_with_key)))
        compressed_size = len(encoded_text)
        compression_ratio_new_iter = compressed_size/uncompressed_size
        print(f"Ratio: {compression_ratio_new_iter}, seed: \"{seed}\"") 

        # If compression ratio is smaller than previous, then replace the ratio
        # Also keep track of how many characters were required to improve ratio
        if compression_ratio_new_iter < compression_ratio_new:
            compression_ratio_new = compression_ratio_new_iter
            if len(increments_required_for_lower_compression_ratio) == 0:
                prev_point = 0
            increments_required_for_lower_compression_ratio.append(i-prev_point)
            prev_point = i

    print(increments_required_for_lower_compression_ratio)
    return


def guess_secret(text_with_key, secret, prefix, letters):
    # Compute base line compression ratio
    seed_base = prefix
    encoder_no_seed = LZ77Encoder(initial_window=seed_base.encode('utf-8'))
    encoded_text = encoder_no_seed.encode_block(DataBlock(list(text_with_key)))
    uncompressed_size = len(text_with_key)*8
    compressed_size_base_seed = len(encoded_text)
    compression_ratio_base_seed = float(compressed_size_base_seed)/float(uncompressed_size)

    # Try to guess the secret
    limit = 2
    n = 0
    min_ratio = compression_ratio_base_seed
    seed = seed_base
    while len(seed) < len(prefix) + len(secret):
        next_seed = seed
        if n >= limit:
            break
        n += 1
        print(f"Current seed: {seed}. Checking increments of {n} characters...")

        # Generate all possible n-element combinations of letters
        combinations_of_n_chars = list(itertools.product(letters, repeat=n))
        assert len(combinations_of_n_chars) == math.pow(len(letters), n)
        
        for chars in combinations_of_n_chars:
            guess = "".join(chars)
            seed_guess = seed + guess
            seed_bin = seed_guess.encode('utf-8')
            encoder = LZ77Encoder(initial_window=seed_bin)
            encoded_text = encoder.encode_block(DataBlock(list(text_with_key)))
            compressed_size = len(encoded_text)
            compression_ratio = float(compressed_size)/float(uncompressed_size)

            # If the compression ratio is less than the previous ratio, modify the seed accordingly
            if compression_ratio < min_ratio:
                min_ratio = compression_ratio
                next_seed = seed_guess
                n = 0
                # print(f"compression rate impoved with new seed: {seed_base}.\n New compression ratio: {compression_ratio}\n")
        
        seed = next_seed
            
    final_guess = seed.replace(prefix, "")
    print(f"Finished looking for a better seed. Final seed: {final_guess}, versus secret: {secret}")
    return final_guess


def run_trials_guess_secret(iterations, text, letters, prefix, L):
    # Try to guess the secret key based on compression ratio
    correct_guess = 0
    half_correct_guess = 0
    for _ in range(iterations):
        # Generate secret
        secret = get_random_string(16, letters)
        
        # Get text
        text = generate_text_with_secret_key(sherlock_novel_cleaned, L, secret, prefix)
        print(text)

        # Guess secret
        guess = guess_secret(text, secret, prefix, letters)

        # Check if correct
        half_secret = secret[0:8]
        if guess == secret:
            correct_guess += 1
            print(f"correct! {guess} = {secret}")
        elif half_secret in guess:
            print(f"half correct :( {guess} != {secret}")
            half_correct_guess += 1
        else:
            print(f"incorrect :( {guess} != {secret}")
    
    print(f"{correct_guess} correct guesses!")
    print(f"{half_correct_guess} half correct guesses!")
    return 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", help="input directory", type=str)
    parser.add_argument("-s", "--seed", help="initialize window from seed input file", type=str)
    args = parser.parse_args()
    
    # Get Sherlock Novel
    sherlock_novel_raw = fetch_sherlock_holmes_novel()

    if sherlock_novel_raw:
        sherlock_novel_cleaned = clean_text(sherlock_novel_raw)

    # Initialize experiment params
    iterations = 5
    letters = string.ascii_lowercase
    prefix = ""
    L = 500

    # Run trials to look at changes in compression ratio, and compression/decompression time
    #run_trials_compute_compression_metrics(iterations, sherlock_novel_cleaned, letters, prefix, L)
    
    # Run trials trying to guess the secret key
    run_trials_guess_secret(iterations, sherlock_novel_cleaned, letters, prefix, L)

    sys.exit(0)
