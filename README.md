# Compression-Security-Project
EE274 Final Project


# Introduction
    I am planning to investigate how data compression creates security vulnerabilities through hardware side channels. Side channels have been a long standing problem for the hardware design community, and they often arise due to data-dependent
hardware optimizations. For example, computer architects implement caching, branch prediction, or arithmetic logic optimizations in order to improve performance of a processor. These optimizations cause an application to use variable timing, 
power, or other hardware resources depending on the data supplied to the application. A side channel arises when an attacker can monitor the hardware resource usage to gain information about secret data, resulting in serious security 
vulnerabilities in a variety of application domains. Therefore, there is a need to implement secure hardware by limiting or obscuring data dependence in hardware optimizations.
    On the other hand, data compression algorithms exploit the probability distribution of the source data to do efficient compression. Therefore compression and security seem to have opposing goals: secure hardware should reduce the visibility 
of data dependence, and efficient compression should capitalize the source data distribution. For example, the compressed size of a file (and perhaps other metrics, such as runtime, power consumption, memory usage, etc.) is entirely dependent on 
the probability distribution of the source data. Therefore it seems to be likely that compression may induce significant side channel security vulnerabilities in their algorithms.
    As an aside, it has recently become standard to model the hardware resource (timing, power, contention, etc.) in security research as a communication channel. This allows researchers to apply information theory metrics, such as entropy and 
mutual information to describe the amount of leakage present for a specific application running on a specific hardware design. This is another interesting tie between data compression research, which uses information theory metrics to quantify 
the efficiency of the compression algorithm, and security, which could use the same metrics to quantify side channel leakage. Determining the best metric for quantifying leakage is still an open question in security research [1], but there is 
undoubtedly overlap in the theory underlying these two fields.


# Literature/Code Review
    There is a significant amount of research discussing side channels that arise from data compression. Kelsey had one of the first works which broadly analyzes the security implications of compression algorithms [2]. The paper discusses how 
lossless compression algorithms create side-channel security vulnerabilities, the practicality of such side-channel attacks, and how and when compression is often used on secret data before encryption. 
    Subsequently, two compression-based attacks, CRIME [3] and BREACH [4], were introduced in 2012 and 2013. Both of these two attacks relied on LZ77 and Huffman compression in order to steal private user information over the web. CRIME uses a 
side channel generated from the compression ratio of compressed TLS requests to recover the headers from HTTP requests. Since headers often contain cookies, an attacker would be able to steal a user’s login. While this attack was quickly 
mitigated by disabling TLS compression, another attack, BREACH, uses the compression ratio of HTTP responses, which are commonly compressed using gzip. For a web application to be vulnerable to BREACH, its requests must be served with HTTP-level 
compressed responses and reflect both user-input and a secret in HTTP response bodies. User input is key, as it allows for an attacker to guess one character at a time and learn the secret by looking at the compression ratio of the response. 
Another attack, HEIST [5], builds on CRIME and BREACH to show that the length of HTTP responses can be leaked without an attacker having access to the victim’s network. 
    While CRIME, BREACH, HEIST, and all other related attacks focus solely on the information leaked due to changes in compression ratio and look at HTTP traffic in particular, there are more recent works which look at compression side channels
in other applications. For example Schwarzl et al. exploit timing side channels in compression algorithms [6]. Using decompression time, they show information about the source data, such as entropy and position of compressible strings, are 
leaked. Further this work looks into broader applications beyond HTTP traffic, including memory-compression, databases, file systems, and others. 
    GPU.zip [7] is another recent compression-based side channel attack, which is based on software transparent compression in both integrated and discrete GPUs. This means that there are compression algorithms running on the GPU which are not 
software visible, and therefore cannot be disabled by the programmer. The attack shows that the GPU compression schemes induce data-dependent DRAM traffic and cache footprints, which leaks information about the source data. In their case, an 
attacker is able to infer the values of individual pixels of a webpage that it does not have access to programmatically. Another recent and novel compression-based attack is Dbreach [8], which can extract information about plaintext in a 
compressed database with limited access to the compressed text. They introduce techniques to reduce noise and heuristics regarding how to generate a good guess of the secret, which, again, must be co-located with the source data.
    Lastly, as more hardware optimizations are proposed in order to improve performance, there is a need to consider these optimizations’ security implications before they are implemented in hardware. One example of this is SafeCracker [9], which 
evaluates the security vulnerabilities of compressed caches. While compressed caches are not yet deployed in hardware, more processors have recently included compression at some level of the memory hierarchy. This paper investigates the security 
properties of compressed caches, and in particular, how they reveal information of program data. In particular they propose an attack where there is attacker-controlled data co-located with secret data in a compressible cache, and using the 
compression ratio (they call it “compressibility”), they are able to learn about the content of the secret data. 
    Many of these attacks look similar to the original compression side channel attacks proposed over a decade ago: some attacker controlled data is compressed with victim data, and subsequently the attacker is able to learn about secret data by 
looking at the compression ratio. However, as compression continues to be implemented more widely in hardware systems, it is imperative to consider the security implications that come with novel applications of data compression in hardware 
optimizations. 
    There has also been some interesting work looking at mitigating compression side channel attacks. Two obvious mitigations include disabling compression entirely or isolating secret data and user controlled data to be compressed independently. 
Other proposed schemes involve simultaneous encryption and compression, including SecOComp’s [cite] chaos-based encryption and compression scheme. However, it is unclear how efficient these schemes are in practice. Overall, the mitigations I 
found do not use novel and/or interesting compression algorithms in order to prevent compression-based side channel leakage, and therefore I will not focus on them for this project. 


# Methods
    I plan to show quantitatively how a side channel can arise from compression algorithms. While implementing a full scale attack may not be feasible for this project, I plan to implement a basic model of a side channel in order to reveal how 
compression can be used to leak secret information from an application. Much of the related work assumes that the attacker can co-locate data with the victim data to be compressed together. Therefore I will show that by modifying user input, such 
as a seed file or a source data probability distribution, some information can be learned about the compressed data. Starting with LZ77, I will show how one could use the compression ratio with a user-provided seed file to guess a secret in the 
source data. Specifically I will look at metrics such as the compression ratio, compression time, and decompression time, in order to learn more information by altering the attacker-controlled input. 
    Additionally, I plan to extend this methodology to at least one other compression algorithm. In this case, I want to be able to compare how different compression algorithms may be more or less prone to side channel leakage than others. After 
collecting information about the side channel, including compression/decompression time and compression ratio, I plan to analyze the data to see if there are any statistically significant trends with respect to changing the attacker controlled 
inputs. Qualititatively, I hope to be able to predict a secret key in a block of text based on the compression ratio with various seed inputs. 
    Time permitting, I would like to consider how information theory metrics can describe the side channel leakage. For example, is there a way to model the mutual information between the attacker and the source data through the side channel? How 
might we use probability models in order to measure or quantify leakage in order to use metrics such as mutual information?


# Progress Report
    First, I spent a significant amount of time reviewing the literature regarding the potential security vulnerabilities that arise from compression algorithms. I reviewed prior work looking at how compression algorithms have been used 
historically to induce security vulnerabilities. I also reviewed more current research looking at potential future compression vulnerabilities when compression is implemented in hardware or systems, such as GPUs, databases, and memory hierarchy 
elements. 
    On the implementation side, I began working on code to measure the compression ratio, compression time, and decompression time for LZ77 encoding and decoding with various attacker-inputted seed files. It is immediately apparent that with more
characters of the “secret key” used in the seed file, the compression ratio decreases. I hope to gather more data and generate plots to show how this might allow an attacker to use the compression ratio to gain information about a secret key. My
goal is to be able to guess the secret key with some accuracy by repeatedly supplying different guesses as the seed and using the compression ratio. 
    The plan for the remaining weeks is to collect the above data. Subsequently, I hope to run a similar experiment using other encoding algorithms, such as Huffman or Arithmetic, and see if by changing a part of the source data distribution, I 
can affect the compression ratio. This will reveal differences in how compression algorithms may be more or less vulnerable to side channel leakage.


# References
[1] Benjamin Wu, Aaron B. Wagner, and G. Edward Suh. 2020. ”A Case for Maximal Leakage as a Side Channel Leakage Metric.” CoRR abs/2004.08035 (2020). arXiv:2004.08035 https://arxiv.org/abs/2004.08035

[2] J. Kelsey, “Compression and information leakage of plaintext,” in FSE, 2002.

[3] J. Rizzo and T. Duong, “The CRIME attack,” Presented at Ekoparty 2012, Sep. 2012, slides online: https://docs.google.com/presentation /d/11eBmGiHbYcHR9gL5nDyZChu-lCa2GizeuOfaLU2HOU/edit.

[4] Gluck, N. Harris, and A. Prado, “BREACH: Reviving the CRIME attack,” Presented at Black Hat USA 2013, Aug. 2013, whitepaper online: https://breachattack.com/resources/BREACH%20-%20SSL,%20gone%20in%2030%20seconds.pdf. 

[5] Mathy Vanhoef and Tom Van Goethem. Heist: Http encrypted information can be stolen through tcp-windows. In Black Hat US Briefings, Location: Las Vegas, USA, 2016.

[6] M. Schwarzl, P. Borrello, G. Saileshwar, H. Muller, M. Schwarz, and D. Gruss, “Practical timing side channel attacks on memory compression,” in S&P, 2023. 

[7] Y. Wang, R. Paccagnella, Z. Gang, W. Vasquez, D. Kohlbrenner, H. Shacham, and C. Fletcher, “GPU.zip: On the Side Channel Implications of Hardware-Based Graphical Data Compression” in S&P, 2024.

[8] M. Hogan, Y. Michalevsky, and S. Eskandarian, “Dbreach: Stealing from databases using compression side channels,” in S&P, 2023. 

[9] P.-A. Tsai, A. Sanchez, C. W. Fletcher, and D. Sanchez, “Safecracker: Leaking secrets through compressed caches,” in ASPLOS, 2020.
