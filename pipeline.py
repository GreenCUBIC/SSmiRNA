import random
import sys
import os
import getopt
import numpy as np
from sklearn.ensemble import *
from classes.FeatureSet import *
from sklearn.externals import joblib
import smote
from subprocess import call

m=0
for n in range (10, 150):
 #n=10
 ##POS
    m=m+1
    call('mkdir '+str(m), shell=True)
    os.chdir(str(m))
    call('mkdir'+ ' ids', shell=True)	
    experiment=str(n)+"_pos.csv"
    def random_line(fname):
        lines=open(fname).readlines()
        return random.choice(lines)
    store=[]
    for i in range (0,5):
        store.append(random_line('80%positive.csv'))

    oldfile=str(n-5)+"_pos.csv"
    store2=[]
    infile=open(oldfile)
    for line in infile:
        store2.append(line)


    for line in store:
        if line not in store2:
            store2.append(line)
    outfile=open(experiment,"w")
    for line in store2:
        outfile.write(line)
    outfile.close()
    call('cp ' +experiment+ ' ids', shell=True)

    outfile=open(experiment,"w")
    for line in store2:
        nline=str(line)
        text = nline.partition(">")[0]
        outfile.write(text)
        outfile.write('\n')
 ###NEG
    experiment2=str(n)+"_neg.csv"
    store3=[]
    for i in range (0,5):
        store3.append(random_line('80%negative.csv'))

    oldfile2=str(n-5)+"_neg.csv"
    store4=[]
    infile=open(oldfile2)
    for line in infile:
        store4.append(line)


    for line in store3:
        if line not in store4:
            store4.append(line)
    outfile=open(experiment2,"w")
    for line in store4:
        outfile.write(line)
    outfile.close()
    call('cp ' +experiment2+ ' ids', shell=True)

    outfile=open(experiment2,"w")
    for line in store4:
        nline2=str(line)
        text2 = nline2.partition(">")[0]
        outfile.write(text2)
        outfile.write('\n')


    fs = FeatureSet()
    stage=m
    fs.load(experiment, patternClass = "miRNA")
    fs.add_instances(experiment2, patternClass = "pseudo")
    #expression:
    fs.select_features(range(216,225))
    #sequence:
    #fs.select_features([1,2,4,5,10,14,19,21,25,26,27,30,37,39,40,43,44,65,125,140,175,179,186,189,191,192,196,200,202,203,207,214 ])
    fs.libsvm_scale()
    fs.export(stage+"/90_expression_pos.csv", "real")
    fs.export(stage+"/90_expression_neg.csv", "pseudo")
    fs.export(stage+"/90_expression.csv")


    numFolds = 10
    outPath = "expression_cotrain"
    stage=m

    posTrainLines = open("mohsen/cotrain_test_accum/"+stage+"/exp/90_expression_pos.csv", 'r').readlines()[1:]
    negTrainLines = open("mohsen/cotrain_test_accum/"+stage+"/exp/90_expression_neg.csv", 'r').readlines()[1:]
    posTestLines = open("mohsen/80-20-hsa1/20_expression_pos.csv", 'r').readlines()[1:]
    negTestLines = open("mohsen/80-20-hsa1/20_expression_neg.csv", 'r').readlines()[1:]

    posTraining = np.array([[float(y) for y in x.split(',')[:-1]] for x in posTrainLines])
    negTraining = np.array([[float(y) for y in x.split(',')[:-1]] for x in negTrainLines])
    posTest = np.array([[float(y) for y in x.split(',')[:-1]] for x in posTestLines])
    negTest = np.array([[float(y) for y in x.split(',')[:-1]] for x in negTestLines])

    pList = []

    # Use SMOTE to deal with class imbalance
    posTraining = smote.SMOTE(posTraining, 100*(len(negTraining)/len(posTraining)), 5)
    # Build a single negative+positive training set
    trainingArray = np.concatenate((posTraining, negTraining))
    trainingClasses = np.array(['1']*len(posTraining) + ['0']*len(negTraining))
    # Build a single negative+positive test set
    testArray = np.concatenate((posTest, negTest))
    testClasses = np.array(['1']*len(posTest) + ['0']*len(negTest))
    # Build classifier on training data
    rf = RandomForestClassifier(n_estimators = 500)
    rf.fit(trainingArray, trainingClasses)

    # joblib.dump(rf, "smirpdeep_model.pkl")
    # Get results for test set
    predictions = rf.predict_proba(testArray)
    predictions = np.hstack((predictions, np.atleast_2d(testClasses).T))
    allPredictions = predictions

    allPredictions = sorted(allPredictions, key = lambda x : x[0])

    print len(allPredictions)


    with open("mohsen/cotrain_test_accum/"+stage+"/exp/"+outPath+".sresults", 'w') as out:
        for p in allPredictions:
            out.write(str(p[0]) + "\t" + str(p[1])+'\t' + p[2] + '\n')

    ci = float(len(negTestLines)) / float(len(posTestLines))
    print "Class imbalance:", ci

    spec = 1.0
    sens = 0.0
    with open("mohsen/cotrain_test_accum/"+stage+"/exp/"+outPath+"_roc.tsv", 'w') as out:
        # out.write('1-spec\tsens\tprec\n')
        for p in allPredictions:
            if p[2] == '1':
                sens += float(1)/float(len(posTestLines))
            else:
                spec -= float(1)/float(len(negTestLines))
            out.write(str(1.0-spec)+'\t'+str(sens)+'\t'+str(sens / (sens + (1.0-spec)*ci))+'\n')


