# Compression-Security-Project
EE274 Final Project


# Introduction
I am investigating how data compression interplays with hardware security, specfically consdering hardware side channels. Side channel leakage has been a long standing problem for the hardware design community. Often computer architects implements data-dependent hardware optimizations, such as caching, branch prediction, or arithmetic logic optimizations. These optimizations cause the same application to use variable timing, power, or contention depending on the input data to the application. A side channel arises when an attackers can monitor the hardware resource usage to gain information about secret data. As a result, hardware side channels create serious security vulnerabilities in a variety of application domains. Therefore, computer architecutre try to implement secure processors by limiting or obscuring data dependence in hardware resource usage.
 On the other hand, data compression algorithms exploit the probability distribution of the source data to efficiently compress the source’s content. These seem to be quite opposing goals: one which wants to reduce the visibility of data dependence, and one that wants to capitalize on it. For example, the compressed size of a file (and perhaps other metrics, such as runtime, power consumption, memory usage, etc.) is entirely dependent on the content of the source data. Therefore it seems to be likely that compression may induce novel security vulnerabilities.
Additionally, it has recently become standard to model the hardware resource as a communication channel. This allows researchers to apply information theory metrics, such as entropy and mutual information to describe the amount of leakage present for a specific application running on a specific hardware design. This is another interesting tie between data compression research, which uses information theory metrics to quantify the quality of compression algorithm used, with security, which could use the same metrics to more precisely quantify the side channel leakage. Determining the best metric in the security research community is still an open question [cite], but there is no doubt that there is overlap in the considerations of these two fields.


# Literature/Code Review
[2002 paper]
Two compression-based attacks, CRIME [cite] and BREACH [cite], were introduced in 2012 and 2013. Both of these two attacks relied on LZ77 and Huffman compression in order to private user information. CRIME uses the compression ratio from compressed TLS requests to recover the headers from HTTP requests. While this attack was quickly mitigated by disabling TLS compression, BREACH uses the compression ratio of HTTP responses, which are commonly compressed using gzip. For a web application to be vulnerable to BREACH, its requests must be served with HTTP-level compressed responses and reflect both user-input a secret in HTTP response bodies. User input is key, as it allows for an attacker to guess one character at a time and learn the secret by looking at the compression ratio of the response. Another attack, HEIST [cite], builds on CRIME and BREACH to show that the length of HTTP responses can be leaked without an attacker having access to the victim’s network. 
While CRIME, BREACH, HEIST, and all other related attacks focus solely on the information leaked due to changed in compression ratio and look at HTTP traffic in particular, there are more recent works which look at compression side channels in other applications. For example Schwarzl et al. exploit timing side channels in compression algorithms [cite]. Using decompression time, they show information about the compressed data, entropy of uncompressed data and other aspects, such as the position of compressible data, are leaked. Further this work looks into broader applications beyond HTTP traffic, including memory-compression, databases, file systems, and others. 
GPU.zip is a more recent compression-based side channel attack, which found that both integrated and discrete GPUs have software transparent compression. This means that there are compression algorithms running on the GPU which are not visible, and therefore cannot be disabled by the programmer. The attack shows that the GPU compression schemes induce data-dependent DRAM traffic and cache footprints, which leaks information about the source data. In their case, an “attacker” webpage is able to infer the values of individual pixels that it does not have access to programmatically.
Lastly, as more hardware optimizations are proposed in order to improve performance, there is a need to consider novel optimizations with security in mind before they are deployed in real hardware. One example of this is SafeCracker [cite], which evaluates the security vulnerabilities of compressed caches,  looking at  another interesting work in side channel compression 
[cache compression]
[dbreach for data bases?]
There is some interesting work in mitigating of compression side channel attacks. Two obvious mitigations include disabling compression entirely or isolating secert data and user controlled data to be compressed independently. Other proprosed schemes involve simultaneous encryption and compression, including SecOComp’s [cite] chaos-based encryption and compression scheme. However, it is unclear how efficient these schemes are in practice. Overall, the mitigations I found do not use novel and/or interesting compression algorithms in order to prevent compression-based side channel leakage, and therefore I will not focus on them for this project. 


# Methods
I plan to implement a basic model of a side channel in order to reveal how compression can be used to leak secert information from an application. In general, many of the above related work assume that the attacker can colocated data with the victim data to be compressed together. Therefore rather than colocating data with the source data, I plan to allow the user to input a seed file of their choice. Then based on the compression time, decompression time, and compression ratio, I want to see if certain compression algorithms can leak more or less data depending on the user controlled seed input files. I plan to look at various compression algorithms in order to explore if some are more vulnerable to side-channel leakage than others. Finally, I plan to run some experiments to see if I can guess an attacker secret string by interatively compressing with different strings. 
Time permitting, I would like to consider how information theory metrics can describe the side channel leakage. For example, is there a way to model the mutual information between the attacker and the source data through the side channel. How might we use probability models in order to measure or quantify leakage in order use metrics such as mutual information?


# Progress Report

Code: eek.


# References

Benjamin Wu, Aaron B. Wagner, and G. Edward Suh. 2020. ”A Case for Maximal Leakage as a Side Channel Leakage Metric.” CoRR abs/2004.08035 (2020). arXiv:2004.08035 https://arxiv.org/abs/2004.08035

J. Rizzo and T. Duong, “The CRIME attack,” Presented at Ekoparty 2012, Sep. 2012, slides online: https://docs.google.com/presentation /d/11eBmGiHbYcHR9gL5nDyZChu-lCa2GizeuOfaLU2HOU/edit.

Gluck, N. Harris, and A. Prado, “BREACH: Reviving the CRIME attack,” Presented at Black Hat USA 2013, Aug. 2013, whitepaper online: https://breachattack.com/resources/BREACH%20-%20SSL,%20gone%20in%2030%20seconds.pdf. 

J. Kelsey, “Compression and information leakage of plaintext,” in FSE, 2002.

M. Hogan, Y. Michalevsky, and S. Eskandarian, “Dbreach: Stealing from databases using compression side channels,” in S&P, 2023. 

M. Schwarzl, P. Borrello, G. Saileshwar, H. Muller, M. Schwarz, ¨ and D. Gruss, “Practical timing side channel attacks on memory compression,” in S&P, 2023. 

P.-A. Tsai, A. Sanchez, C. W. Fletcher, and D. Sanchez, “Safecracker: Leaking secrets through compressed caches,” in ASPLOS, 2020.
