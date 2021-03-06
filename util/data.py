import os
import logging
from collections import defaultdict
import numpy as np
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical

from util import preprocess


class Data(object):

    token2idx = {'PADDING': 0, 'UNKNOWN': 1}
    feature2idx = defaultdict(lambda : {'PADDING': 0})
    label2idx = {'PADDING': 0}
    tokenIdx2charVector = []
    wordEmbedding = []

    sentences = None
    labels = None
    features = None

    def __init__(self, inputPathList, freqCutOff=1):

        tokenFreq = preprocess.tokenFrequency(inputPathList)
        for token, freq in tokenFreq.items():
            if token not in self.token2idx and freq >= freqCutOff:
                self.token2idx[token] = len(self.token2idx)
        self.feature2idx, self.label2idx = preprocess.featureLabelIndex(inputPathList)
        self.char2idx = preprocess.getChar2idx()

        tokenLengthDistribution = preprocess.tokenLengthDistribution(self.token2idx)
        self.maxTokenLen = preprocess.selectPaddingLength(tokenLengthDistribution, ratio=0.99)
        logging.info('Max token length: ' + str(self.maxTokenLen))

        sentenceLengthDistribution = preprocess.sentenceLengthDistribution(inputPathList)
        self.maxSentenceLen = preprocess.selectPaddingLength(sentenceLengthDistribution, ratio=0.99)
        logging.info('Max sentence length: ' + str(self.maxSentenceLen))

        self.vocabSize = len(self.token2idx)
        logging.info('Vocabulary size: ' + str(self.vocabSize))

        self.labelDim = len(self.label2idx)
        logging.info('Label dim: ' + str(self.labelDim))

        self.initToken2charVector()
        self.initWordEmbedding()

    def initToken2charVector(self):
        tokenIdx2charVector = []
        for token, idx in sorted(self.token2idx.items(), key=lambda kv: kv[1]):
            if idx != 0:
                charVector = list(map(lambda c: self.char2idx.get(c, 1), token))    # 1 for UNKNOWN char
            else:
                charVector = [0]  # PADDING
            tokenIdx2charVector.append(charVector)

        self.tokenIdx2charVector = np.asarray(pad_sequences(tokenIdx2charVector, maxlen=self.maxTokenLen))
        logging.debug(self.tokenIdx2charVector.shape)

    def initWordEmbedding(self, dim=100):
        """        
        The tokens in the word embedding matrix are uncased 
        """
        word2vector = preprocess.loadWordEmbedding('data/glove.6B.100d.txt', dim=dim)
        for token, idx in sorted(self.token2idx.items(), key=lambda kv: kv[1]):
            if idx >= 2:
                token = token.lower()
            vector = word2vector.get(token, np.random.uniform(-0.25, 0.25, dim))
            self.wordEmbedding.append(vector)
        self.wordEmbedding = np.asarray(self.wordEmbedding)
        logging.debug(self.wordEmbedding[0])
        logging.debug(self.wordEmbedding.shape)



    def loadCoNLL(self, filePath):

        sentences = [[]]
        features = defaultdict(list) #TODO: load features
        labels = [[]]

        with open(filePath, 'r', encoding='utf-8') as inputFile:

            for line in inputFile:
                line = line.strip()
                if not line:
                    sentences.append([])
                    labels.append([])

                else:
                    data_tuple = line.split('\t')

                    token = data_tuple[0]
                    tokenIdx = self.token2idx.get(token, 1) # 1 for UNKNOWN
                    sentences[-1].append(tokenIdx)

                    labelIdx = self.label2idx[data_tuple[-1]]
                    labels[-1].append(labelIdx)

        # Pad sentence to the longest length
        self.sentences = pad_sequences(sentences, maxlen=self.maxSentenceLen)

        del sentences

        # Transform labels to one hot encoding
        self.labels = np.expand_dims(pad_sequences(labels, maxlen=self.maxSentenceLen), -1)





