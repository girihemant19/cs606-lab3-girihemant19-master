#!/usr/bin/env python
# coding: utf-8

# In[1]:


# The steps required for this program are#
# 1. Convert each test file into a set of shingles.
#    - Form shingles by taking 3 words together.
#    - Encode shingles to 32 bit integers. (Can use a CRC32 hash for this)
# 2. Compute all Jaccard similarities.
# 3. Compute the MinHash signature for each document.
#    - Use the Fast MinHash algorithm as dicussed in class so that explicit 
#      permutations of all shingle IDs are not required.
# 4. Compare MinHash signatures to one another for finding plagiarism.
#    - Compare the MinHash signatures by finding out the number of components in which
#      the signatures are equal and taking a average of them.
#    - Show the pairs of documents where similarity is greater than 0.5.

import os
import re
import random
import time
import binascii
import sys

# Set the number of rows (or components) in the MinHash signatures. Will also need this
# many hash functions.
numHashRows = 10;

# Now run the MinHash algorithm for different portions of the dataset. /data directory has
# different data files with 100, 1000, and 10,000 documents.

numDocs = 1000 # Start with 100. Meaning there are 100 articles in 1 data file (same as 100 individual docs).
dataFile = "./data/docs_" + str(numDocs) + ".train"
plagFile = "./data/docs_" + str(numDocs) + ".plag"

# Create ground truths from the plagiarism results already provided.
# They will be useful later on for checking true and false positives.

plagiarisms = {}

# Open the plag file.
f = open(plagFile, "r+")

# For each pair reported
for line in f:
  
  # Remove new-line character if present
  if line[-1] == '\n':
      line = line[0:-1]
      
  docs = line.split(" ")

  # Keep a map of the two documents
  plagiarisms[docs[0]] = docs[1]
  plagiarisms[docs[1]] = docs[0]

# Now convert the documents to shingles

print("Creating Shingles...")

# Keep a current ID for the current shingle. When a new shingle is encountered in
# the dictionary, we will update this.

currentShingleID = 0

# Create a dictionary for the articles having a mapping of the article identifier
# for example t123, to the list of the shingle IDs.

documentShingleSets = {};
  
# Open the data file.
f = open(dataFile, "r+")

documentNames = []

numShingles = 0

for i in range(0, numDocs):

  # ADD CODE HERE TO DO THE FOLLOWING:

  # Read akk the words (may need splitting)
    words = f.readline().split(" ")
  # Maintain a list of document IDs (article IDs)
    docID = words[0]
    documentNames.append(docID)
    del words[0] 
  # Create a set of shingles called shinglesInDocument
    shinglesInDoc = set()
  # For each word in document create a shingle by combining 3 consecutive
  # words together. This is where the Python set will help as it will 
  # automatically remove duplicate shingles.
    for index in range(0, len(words) - 2):
        shingle = words[index] + " " + words[index + 1] + " " + words[index + 2]

  # Use the binascii library to hash every shingle to a 32 bit integer.
        crc = binascii.crc32(shingle.encode('utf-8')) & 0xffffffff
  # Read binascii manual to find out how to use them.
  # Add the hashed value to the set.
        shinglesInDoc.add(crc)

  # Now add the completed set of shingles to the documentShingleSets dictionary.
    documentShingleSets[docID] = shinglesInDoc
  # Keep a count of the total number of shingles found in numShingles.
    numShingles = numShingles + (len(words) - 2)
# Close the data file.  
f.close()  

print('\nAverage shingles per document: %.2f' % (numShingles / numDocs))


# In[2]:


# Now we are going to compute the similarity values. For that we need to store the
# values in a matrix which you know will be sparse. So, we are going to store it
# in the conventional matrix way (using a row0major implementation).

# Second optimized way is to use a triangular matrix as it consumes only half of
# size of a full matrix. BONUS POINTS IF YOU DO THIS.

#Find out how many elements you will need
totalSize = int(numDocs * (numDocs - 1) / 2)
# Now intiialize two lists to store 2 similarity values. 
# 1. JaccSim to store the Jaccard Similarity
# 2. MinHashSim will be the estimated similarity by comparing the MinHash signatures.

JaccSim = [0 for x in range(totalSize)]
MinHashSim = [0 for x in range(totalSize)]

# Define a function to map a 2D matrix co-ordinate to a 1D index.
# If you use triangular matrix, then this logic will change. The idea
# is explained in MMDS book Chap 6.
def getMatrixIndex(i, j):
  # If i == j that's an error.
  if i == j:
    sys.exit(1)
  # If j < i just swap the values.
  if j < i:
    temp = i
    i = j
    j = temp
  
  # Calculate the index within the triangular array.
  # This fancy indexing scheme is taken from pg. 211 of:
  # http://infolab.stanford.edu/~ullman/mmds/ch6.pdf
  # But I adapted it for a 0-based index.
  # Note: The division by two should not truncate, it
  #       needs to be a float. 
  k = int(i * (numDocs - (i + 1) / 2.0) + j - i) - 1
  
  return k


# In[3]:


# ONE COMPARISON WILL BE TO STUDY HOW MUCH JACCARD SIMILARITY IS SLOWER THAN
# COMPUTING MIN HASH. INSERT TIMERS TO DO A COMPARISON

print("\nCalculating Jaccard Similarities...")


# For every document pair...
for i in range(0, numDocs):
    if (i % 100) == 0:
        print("  (" + str(i) + " / " + str(numDocs) + ")")
    s1 = documentShingleSets[documentNames[i]]
      # Get shingle set for document i 
    for j in range(i + 1, numDocs):
            # Get shingle set for document j
            s2 = documentShingleSets[documentNames[j]]
        
          #Calculate and store the Jaccard Similarities
            JaccSim[getMatrixIndex(i, j)] = (len(s1.intersection(s2)) / len(s1.union(s2)))# ADD YOUR CODE

# May need to delete JaccSim as it can be a very big matrix. Especially for larger 
# document sizes.
# del JaccSim
del JaccSim


# In[4]:


# Now perform Min Hashing. AGAIN YOU CAN INSERT TIMERS TO FIND OUT THE SPEED DIFFERENCE
# WITH JACC SIM.

print('\nGenerate random hash functions...')

# Store the maximum shingle ID
maximumShingleID =2**32-1 # ADD CODE

# FOR HASH FUNCTIONS IT IS BETTER TO USE PRIME NUMBERS.
# THIS WILL BE SIMILAR TO SETTING UP THE INFINITY VALUE OF THE LARGEST POSSIBLE HASH.
# ALSO THIS WILL REDUCE POSSIBLE COLLISIONS.
# YOU CAN FIND A PRIME NUMBER GREATER THAN maximumShingleID at the following URL.
# http://compoasso.free.fr/primelistweb/page/prime/liste_online_en.php

oneLargePrime = 4294967311# LOOK UP AND ADD


# The hash function we will use will be of the following form:
#   h(x) = (a*x + b) % c
# Where 'x' is the input value, 'a' and 'b' are random coefficients, and 'c' is
# a prime number just greater than maximumShingleID.

# Now generate a list of 'k' random coefficients while also ensuring that the
# random number you pick for 'a' and 'b' is unique.

def generateRandomCoefficients(k):
  #List of k random coefficients
  randomCoeffList = []
  # ADD CODE TO FILL UP randomCoeffList
  while k > 0:
    # Get a random shingle ID.
    randIndex = random.randint(0, maximumShingleID) 
  
    # Ensure that each random number is unique.
    while randIndex in randomCoeffList:
      randIndex = random.randint(0, maximumShingleID) 
    
    # Add the random number to the list.
    randomCoeffList.append(randIndex)
    k = k - 1
    
  return randomCoeffList

# For the 'numhashRows' number of hash functions, pick different 'a' and 'b'

coefficientsA=generateRandomCoefficients(numHashRows)
coefficientsB=generateRandomCoefficients(numHashRows)


# In[5]:


print('\nComputing MinHash signatures for all documents...')

# Create a list of documents as signature vectors
signatures = []

# Now write the code for the Fast MinHash algorithm. Rather than finding the random
# permutations of all shingles, just find out the hashes for the IDs that are 
# actually present in the document. Then take the lowest hash code value. This will
# be the index of the first shingle that you will encounter in the randomized order.
# For each document...
for docID in documentNames:
  
  # Get the shingle set for this document.
  shingleIDSet = documentShingleSets[docID]
  
  # The resulting minhash signature for this document. 
  signature = []
  
  # For each of the random hash functions...
  for i in range(0, numHashRows):
    
    minHashCode = oneLargePrime + 1
    
    # For each shingle in the document...
    for shingleID in shingleIDSet:
      #the hash function.
      hashCode = (coefficientsA[i] * shingleID + coefficientsB[i]) % oneLargePrime 
      
      # Track the lowest hash code seen.
      if hashCode < minHashCode:
        minHashCode = hashCode

    # Add the smallest hash code value as component number 'i' of the signature.
    signature.append(minHashCode)
  
  # Store the MinHash signature for this document.
  signatures.append(signature)


# In[6]:


# NOW COMPARE THE MINHASH VALUES FOR ALL DOCUMENTS

# ADD CODE FOR FOLLOWING:
# For all the documents
for i in range(0, numDocs):
    # Get signature for 'ith' document
    sign1 = signatures[i]
    # For every other document
    for j in range(i + 1, numDocs):
        sign2 = signatures[j]
        count = 0
        # Count the number of positions in the minhash signature where they are equal.
        for k in range(0, numHashRows):
            count = count + (sign1[k] == sign2[k])
    # Record the average number of positions in which they matched and store in 'MinHashSim'.
        MinHashSim[getMatrixIndex(i, j)] = (count / numHashRows)


# In[8]:


# Now display similar document pairs
# Initialize variables for true positives and false positives.

tp = 0
fp = 0
  
# SET THRESHOLD
threshold = 0.5

# ADD CODE FOR FOLLOWING

# FOR i in 0 to ALL DOCUMENTS
    # FOR j in i+1 to ALL DOCUMENTS
for i in range(0, numDocs):  
  for j in range(i + 1, numDocs):
    # Get MinHashSim for the pair (i, j)
    approx = MinHashSim[getMatrixIndex(i, j)]
    if approx > threshold:
        # Get JaccSim of the pair (i,j)
        str1 = documentShingleSets[documentNames[i]]
        str2 = documentShingleSets[documentNames[j]]
        Jaca = (len(str1.intersection(str2)) / len(str1.union(str2)))
        # Print both
        print(approx, Jaca)
        # find out by comparing with ground truth if it is a true positive
        # or a false positive. Display their counts.
        if plagiarisms[documentNames[i]] == documentNames[j]:
            tp = tp + 1
        else:
            fp = fp + 1
print("TP is:  " + str(tp) + " / " + str(int(len(plagiarisms.keys()) / 2)))
print("FP is: " + str(fp))





