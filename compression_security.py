import argparse
import os
import sys
import numpy
import time
import random
import string

# Append scl to path in order to import encoders and decoders
sys.path.append('../stanford_compression_library')
from scl.compressors.lz77 import LZ77Encoder, LZ77Decoder
from scl.core.data_block import DataBlock


def generate_text_with_secret_key():
    # Generate a random secret key
    # Currently using a predetermined secret, but want to use a randomly generated secret
    secret_key = "ZWtkH7fgGwRsmVob"

    # Create a block of random English text
    text = """
    In the midst of the bustling city, where skyscrapers touched the clouds and the hum of urban life echoed through the streets, there existed a hidden realm. Beneath the surface of routine and mundane activities, a secret key was waiting to be discovered.

    As the sunlight filtered through the towering buildings, casting long shadows on the pavement, the key remained elusive, camouflaged within the ebb and flow of daily existence. Only those with a keen eye for detail and a penchant for unraveling mysteries could discern its presence.

    The city's heartbeat, a rhythmic blend of car horns and distant conversations, seemed to conceal the clandestine nature of the key. Yet, within the cadence of life, a pattern emerged: a subtle arrangement of words and phrases that held the key to unlocking a world of possibilities.

    As day turned to night, and the cityscape transformed into a glittering panorama of lights, the secret key shimmered like a hidden gem. It beckoned to those who dared to venture beyond the surface, promising a glimpse into a realm where encryption met imagination.

    And so, in the heart of the metropolis, amidst the chaos and order interwoven like a complex code, the secret key awaited its discoverer: a cryptographic enigma concealed within the tapestry of urban narratives.
    """

    # Embed the secret key within the text
    text_with_key = text.replace("cityscape transformed ", f"The secret key is {secret_key}")
    binary_text = text_with_key.encode('utf-8')
    return binary_text, secret_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", help="input directory", type=str)
    parser.add_argument("-s", "--seed", help="initialize window from seed input file", type=str)
    args = parser.parse_args()

    # Initialize encoders
    compresstion_time_per_encoder = dict()

    # LZ77 initialization
    secret = "ZWtkH7fgGwRsmVob"
    for i in range(len("ZWtkH7fgGwRsmVob")):
        seed = "The secret key is "
        seed += secret[0:i]
        print(f"seed: {seed}")
        seed_bin = seed.encode('utf-8')
        compresstion_time_per_encoder[f"LZ77Encoder_seed_{i}"] = {"encoder": LZ77Encoder(initial_window=seed_bin), "decoder": LZ77Decoder(initial_window=seed_bin)}

    # Initialize other compressors?

    # Initialize data sets?

    # Loop over files in directory and time the compression with various encoders
    for compressor_name, compressor_dict in compresstion_time_per_encoder.items():
        encoder = compressor_dict.get("encoder")
        decoder = compressor_dict.get("decoder")

        compression_times = []
        decompression_times = []
        text_with_key, key = generate_text_with_secret_key()
        start = time.time()
        encoded_text = encoder.encode_block(DataBlock(list(text_with_key)))
        end = time.time()
        compression_times.append(end - start)
        compresstion_time_per_encoder[compressor_name]["compression_time"] = compression_times

        start = time.time()
        decoded_text = decoder.decode_block(encoded_text)
        end = time.time()
        decompression_times.append(end - start)
        compresstion_time_per_encoder[compressor_name]["decompression_time"] = decompression_times 

        uncompressed_size = sys.getsizeof(text_with_key)
        compressed_size = sys.getsizeof(encoded_text)
        print(uncompressed_size)
        print(compressed_size)
        compression_ratio = float(compressed_size)/float(uncompressed_size)

        print(f"Compression times for {compressor_name} encoder: {compression_times}")
        print(f"Decompression times for {compressor_name} encoder: {decompression_times}")
        print(f"Compression ratios for {compressor_name} encoder: {compression_ratio}")