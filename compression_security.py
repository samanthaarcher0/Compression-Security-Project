import argparse
import os
import sys
import time
import random
import string
import csv
import itertools
import math
import matplotlib.pyplot as plt
import numpy as np

# Append scl to path in order to import encoders and decoders
sys.path.append('../stanford_compression_library')
from scl.compressors.lz77 import LZ77Encoder, LZ77Decoder
from scl.compressors.huffman_coder import HuffmanEncoder, HuffmanDecoder
from scl.compressors.arithmetic_coding import ArithmeticEncoder, ArithmeticDecoder, AECParams
from scl.core.data_block import DataBlock
from scl.core.data_stream import TextFileDataStream
from scl.core.prob_dist import Frequencies


def read_sherlock():
    DATA_BLOCK_SIZE = 50000
    FILE_PATH = "sherlock_ascii.txt"

    # read in DATA_BLOCK_SIZE bytes
    with TextFileDataStream(FILE_PATH, "r") as fds:
        data_block = fds.get_block(block_size=DATA_BLOCK_SIZE)

    text_string = "".join(data_block.data_list)
    text_string1 = ' '.join(text_string.split())
    return text_string1


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


def run_trials_compute_compression_metrics(iterations, text, letters, prefix, L, compression_algorithm, use_seed):
    # Loop through iterations and collect statistics
    compression_stats = []
    compression_stats_array = np.zeros((iterations,32,3))
    for t in range(iterations):
        print(f"running trial {t}")

        # Generate secret
        secret = get_random_string(32, letters)
        
        # Get text
        text_with_key = generate_text_with_secret_key(text, L, secret, prefix)
        print(text_with_key)

        for i in range(len(secret)):
            num_char_of_secret_key = i
            if use_seed == 1:
                seed = prefix + secret[:i]
            elif use_seed == 0:
                seed = prefix + get_random_string(i, letters)
            seed_bin = seed.encode('utf-8')

            if compression_algorithm=="lz77":
                # LZ77 initialization
                encoder = LZ77Encoder(initial_window=seed_bin)
                decoder = LZ77Decoder(initial_window=seed_bin)
                data_block = DataBlock(list(text_with_key))
            elif compression_algorithm=="huffman":
                # Huffman initialization
                text_with_key += seed_bin
                uncompressed_size = len(text_with_key)*8
                data_block = DataBlock(list(text_with_key))
                prob_dist = data_block.get_empirical_distribution(order=0)
                encoder = HuffmanEncoder(prob_dist)
                decoder = HuffmanDecoder(prob_dist)
            elif compression_algorithm=="aes":
                # Arithmetic initialization
                text_with_key += seed_bin
                uncompressed_size = len(text_with_key)*8
                data_block = DataBlock(list(text_with_key))
                params = AECParams()
                freq_model = Frequencies(data_block.get_counts())
                encoder = ArithmeticEncoder(params, freq_model)
                decoder = ArithmeticDecoder(params, freq_model)
            else:
                print("Unsupported compression algorithm specified. Exiting.")
                return

            # Encode text
            start = time.time()
            encoded_text = encoder.encode_block(data_block)
            end = time.time()
            comp_time = end - start

            # Decode text
            start = time.time()
            decoded_text = decoder.decode_block(encoded_text)
            end = time.time()
            decomp_time = end - start

            # Compute ratio
            compressed_size = len(encoded_text)
            compression_ratio = float(compressed_size)/float(uncompressed_size)

            # Append stats
            compression_stats.append([num_char_of_secret_key, comp_time, decomp_time, compression_ratio])
            compression_stats_array[t][num_char_of_secret_key] += [comp_time, decomp_time, compression_ratio]

    # Write compression states to a CSV file
    csv_filename = f"compression_stats_{compression_algorithm}.csv"
    write_compression_stats(compression_stats, csv_filename)
    return compression_stats_array


def write_compression_stats(compression_stats, filename):
    # Initialize csv file
    csv_fields = ['num secret char in seed', 'compression time', 'decompression time', 'compression ratio']

    # Write to csv file 
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w') as csvfile:  
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
        text = generate_text_with_secret_key(text, L, secret, prefix)
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
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-i", "--input_dir", help="input directory", type=str)
    # parser.add_argument("-s", "--seed", help="initialize window from seed input file", type=str)
    # args = parser.parse_args()
    
    sherlock_novel = read_sherlock()

    # Initialize experiment params
    iterations = 1
    letters = string.ascii_lowercase
    prefix = "the secret is "
    L = 500

    # Run trials to look at changes in compression ratio, and compression/decompression time
    compression_algorithm = "Huffman"
    compression_stats_array_no_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 0)
    compression_stats_array_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 1)

    # Run trials trying to guess the secret key
    #run_trials_guess_secret(iterations, sherlock_novel, letters, prefix, L)

    # Creating plot
    plt.style.use('_mpl-gallery')
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    labels = [str(i) for i in range(32)] 

    box_plot_data_seed = []
    box_plot_data_no_seed = []
    for i in range(32):
        box_plot_data_seed.append(compression_stats_array_seed[:,i,2])
        box_plot_data_no_seed.append(compression_stats_array_no_seed[:,i,2])
    bp1 = ax1.boxplot(box_plot_data_seed, patch_artist=True, labels=labels)
    bp2 = ax1.boxplot(box_plot_data_no_seed, patch_artist=True, labels=labels)

    colors = {'blue': bp1, 'purple': bp2}
    for col, bplot in colors.items():
        for item in ['boxes', 'whiskers', 'fliers', 'caps']:
            plt.setp(bplot[item], color=col)
            plt.setp(bplot["medians"], color="red")

    ax1.legend([bp1["boxes"][0], bp2["boxes"][0]], ['Secret colocated with data', 'Random guess colocated with data'], loc='lower right')
    if compression_algorithm == "huffman":
        plt.title("How co-locating secret with data affects Huffman compression ratio")
    elif compression_algorithm == "aes":
        plt.title("How co-locating secret with data affects Arithmetic Coding compression ratio")
    plt.show()





    sys.exit(0)