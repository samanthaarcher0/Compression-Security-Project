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
    # Generate random key
    # Use lowercase letters by default
    if letters == None:
        letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def generate_text_with_secret_key(text, L, secret_key, prefix):
    # Get random index to pull text from novel and get random index to insert secret
    secret_index = random.randint(0, L)
    if len(text) - L > 0:
        start_index = random.randint(0, len(text) - L)
        text = text[start_index:start_index+L]
    else: 
        start_index = 0

    # Embed the secret key within the text at the randomly generated index
    key_with_prefix = prefix + secret_key
    text_with_key = text[:secret_index] + key_with_prefix + text[secret_index+1:]
    binary_text = text_with_key.encode('utf-8')
    return binary_text


def run_trials_compute_compression_metrics(iterations, text, letters, prefix, L, compression_algorithm, use_seed, text_with_key_orig=None, secret_orig=None):
    # Loop through iterations and collect statistics
    compression_stats = []
    compression_stats_array = np.zeros((iterations,32,3))
    for t in range(iterations):
        print(f"Running trial {t}")

        # Generate secret and text if not provided as input
        if text_with_key_orig == None and secret_orig==None:
            secret = get_random_string(32, letters)
            text_with_key = generate_text_with_secret_key(text, L, secret, prefix)
            print(text_with_key)
        # Else use text and secret specified with arguments
        else: 
            text_with_key = text_with_key_orig
            secret = secret_orig

        # For each character in the secret, measure compression ratio for longer seeds
        for i in range(len(secret)):
            num_char_of_secret_key = i
            # If using the secret as the seed, add i characters of the secet to the prefix
            if use_seed == 1:
                seed = prefix + secret[:i]
            # If not using secret as the seed, add i random characters of the secret to the prefix
            elif use_seed == 0:
                seed = prefix + get_random_string(i, letters)
            seed_bin = seed.encode('utf-8')

            # Initialize encoder/decoder with seed or secret
            if compression_algorithm=="lz77":
                # LZ77 initialization
                uncompressed_size = len(text_with_key)*8
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
                # Notes AES is not actually supported, but would be interesting to consider in the future
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


def guess_secret(text_with_key, secret, prefix, letters):
    # Compute base line compression ratio with the seed=prefix
    seed_base = prefix
    encoder_no_seed = LZ77Encoder(initial_window=seed_base.encode('utf-8'))
    encoded_text = encoder_no_seed.encode_block(DataBlock(list(text_with_key)))
    uncompressed_size = len(text_with_key)*8
    compressed_size_base_seed = len(encoded_text)
    compression_ratio_base_seed = float(compressed_size_base_seed)/float(uncompressed_size)

    # Try to guess the secret
    # If 1 character does not provide any improvement in rate, try up to 'limit' characters next guess of the secret
    limit = 2
    n = 0
    min_ratio = compression_ratio_base_seed
    seed = seed_base

    # Keep trying until seed is length of prefix + secret
    while len(seed) < len(prefix) + len(secret):
        next_seed = seed
        if n >= limit:
            break
        n += 1
        print(f"Current seed: {seed}. Checking increments of {n} characters...")

        # Generate all possible n-element combinations of letters
        combinations_of_n_chars = list(itertools.product(letters, repeat=n))
        assert len(combinations_of_n_chars) == math.pow(len(letters), n)
        
        # Guess the next character of the secret by adding it to the existing seed
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
        
        seed = next_seed
    
    # Remove the prefix and ensure that the final seed is the correct length
    # This could be off if on the last character it required more than 1 character to see an lower compression ratio
    final_guess = seed.replace(prefix, "")
    if len(final_guess) > len(secret):
        final_guess = final_guess[0:len(secret)]
    print(f"Finished looking for a better seed. Final seed: {final_guess}, versus secret: {secret}")
    return final_guess


def run_trials_guess_secret(iterations, text, letters, prefix, L):
    # Try to guess the secret key based on compression ratio
    correct_guess = 0
    half_correct_guess = 0
    for i in range(iterations):
        print(f"Iteration: {i}")
        # Generate secret
        secret = get_random_string(16, letters)
        
        # Get text
        text_with_key = generate_text_with_secret_key(text, L, secret, prefix)
        print(text_with_key)

        # Guess secret
        guess = guess_secret(text_with_key, secret, prefix, letters)

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
    
    return correct_guess, half_correct_guess


if __name__ == "__main__":
    # Parse and validate arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", help="target to run", type=str)
    parser.add_argument("-l", "--length", default=500, help="source data length", type=int)
    parser.add_argument("-i", "--iterations", default=1, help="number of iterations to run", type=int)
    parser.add_argument("-p", "--prefix", default="the secret is ", help="prefix prepended to secret key", type=str)
    args = parser.parse_args()
    
    if args.target == None:
        print("You must specify a target")
        sys.exit(0)

    # Initialize experiment params
    sherlock_novel = read_sherlock()
    iterations = args.iterations
    letters = string.ascii_lowercase
    prefix = args.prefix
    L = args.length

    # Run target 
    if args.target == "huffman":
        # Run Huffman trials to look at changes in compression ratio, and compression/decompression time
        compression_algorithm = "huffman"
        compression_stats_array_no_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 0, None, None)
        compression_stats_array_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 1, None, None)

        # Create box plot to emphasize averages over many iterations
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

        ax1.set(
            xlabel='Number of characters in attacker\'s guess (excluding prefix)',
            ylabel='Compression ratio',
        )

        colors = {'blue': bp1, 'purple': bp2}
        for col, bplot in colors.items():
            for item in ['boxes', 'whiskers', 'fliers', 'caps']:
                plt.setp(bplot[item], color=col)
                plt.setp(bplot["medians"], color="red")

        ax1.legend([bp1["boxes"][0], bp2["boxes"][0]], ['Secret colocated with data', 'Random guess colocated with data'], loc='lower right')
        if compression_algorithm == "huffman":
            plt.suptitle("How co-locating secret with data affects Huffman compression ratio")
            plt.title(f"{L} character text and secret prefix is \"{prefix}\"")
        elif compression_algorithm == "aes":
            plt.suptitle("How co-locating secret with data affects Arithmetic Coding compression ratio")
            plt.title(f"{L} character text and secret prefix is \"{prefix}\"")
        plt.show()

    elif args.target == "guess_secret":
        # Run trials trying to guess the secret key
        correct_guess, half_correct_guess = run_trials_guess_secret(iterations, sherlock_novel, letters, prefix, L)
        incorrect_guess = iterations - correct_guess - half_correct_guess
        print(f"{correct_guess} correct guesses!")
        print(f"{half_correct_guess} half correct guesses!")

        # Output pie chart for the number of iterations
        results = list()
        results_labels = list()
        if correct_guess > 0:
            results.append(correct_guess)
            results_labels.append("Correct guesses")
        if half_correct_guess > 0:
            results.append(half_correct_guess)
            results_labels.append("Atleast half correct guesses")
        if incorrect_guess  > 0:
            results.append(incorrect_guess)
            results_labels.append("Incorrect guesses")

        plt.pie(np.array(results), labels = results_labels, autopct='%1.1f%%')
        plt.title(f"Number of correct guesses of secret key out of {iterations} iterations")
        plt.show() 

    elif args.target == "lz77":
        if iterations > 1:
            print("Only support running 1 iteration for this experiment.")
            iterations = 1

        # Run LZ77 trials to look at changes in compression ratio, and compression/decompression time
        # Generate secret and text
        secret = get_random_string(32, letters)
        text_with_key = generate_text_with_secret_key(sherlock_novel, L, secret, prefix)
        print(text_with_key)
        compression_algorithm = "lz77"
        compression_stats_array_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 1, text_with_key, secret)
        compression_stats_array_no_seed = run_trials_compute_compression_metrics(iterations, sherlock_novel, letters, prefix, L, compression_algorithm, 0, text_with_key, secret)

        # Create scatter plot with data
        scatter_plot_data_seed = []
        scatter_plot_data_no_seed = []
        for i in range(32):
            scatter_plot_data_seed.append(compression_stats_array_seed[:,i,2])
            scatter_plot_data_no_seed.append(compression_stats_array_no_seed[:,i,2])
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        locs, labels = plt.xticks()
        plt.xticks(np.arange(0, 32, step=4))  

        ax1.scatter(range(32), scatter_plot_data_seed, s=10, c='b', marker="o", label='Using secret as seed')
        ax1.scatter(range(32), scatter_plot_data_no_seed, s=10, c='r', marker="o", label='Using random characters as seed')
        ax1.grid(axis='y')
        ax1.set(
            xlabel='Number of characters in attacker\'s guess (excluding prefix)',
            ylabel='Compression ratio',
        )
        plt.suptitle("Number of characters of the secret key in seed file vs. LZ77 compression ratio")
        plt.title(f"{L} character text and secret prefix is \"{prefix}\"")
        plt.legend(loc='lower left')
        plt.show()

    sys.exit(0)