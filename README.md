# Compression-Security-Project
EE274 Final Project

See <link to project report> for details.

# Setup

This project is based on Stanford Compression Library (SCL). See instructions for SCL setup in order to reproduce results: https://stanforddatacompressionclass.github.io/notes/scl_tutorial/SCL_tutorial.html

# Running code

There are three different experiments that can be reproduced:

1. LZ77 compression ratio data with increasing number of characters of secret in seed file versus increasing number random characters in seed file. Note this experiment will only run 1 iteration even if more iterations are specified with -i argument. 
2. Huffman compression ratio data with increasing number of characters of secret co-located with source data versus increasing number random characters co-located with source data
3. Guessing secret based on LZ77 compression ratio

Each experiment should show a plot of the data after the experiment has completed. 

It can be rerun with the following command:

`python3 compression_security.py --target <experiment to run> <other arguments>

# Arguments

Here are the arguments to provide to the script:

`-t/--target` (REQUIRED): specify which experiment to run. Options are `lz77`, `huffman`, and `guess_secret`
`-l/--length`: specify the length of the source data before the secret has been inserted. Default = 500 characters
`-i/--iterations`: specify the number of iterations to run the experiment. This only applies for Huffman where multiple trials are required to see statistical significance and guessing the secret.
`-p/--prefix`: specify the attacker-known prefix for the data. Default = "the secret is "

# Other files

As noted above, SCL is required to run this script. Additionally, all experiments take source data from sherlock holmes novel, which is also in this repository. No other files should be required to rerun experiments. 

