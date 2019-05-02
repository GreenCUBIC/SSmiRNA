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

## This section is only required if active learning is used as a solo tool.
## If combined with co-training, the following section must be commented.
##Starting from here
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
##Ending here

##The code above must be replaced with the resulting train/test sets of the co-training method.
##The code for this is available in the co-training file.

fs = FeatureSet()
stage="first run"
fs.load("mohsen/active_hsa1/"+stage+"/20%positive.csv", patternClass = "miRNA")
fs.add_instances("mohsen/active_hsa1/"+stage+"/20%negative.csv", patternClass = "pseudo")
#active:
fs.select_features([1,18,25,26,34,38,39,43,44,45,139,153,215,216,217,219,220,222,224 ])
fs.libsvm_scale()
fs.export("mohsen/active_hsa1/"+stage+"/20_active_pos.csv", "real")
fs.export("mohsen/active_hsa1/"+stage+"/20_active_neg.csv", "pseudo")
fs.export("mohsen/active_hsa1/"+stage+"/20_active.csv")


fs = FeatureSet()
#stage="first run"
fs.load("mohsen/active_hsa1/"+stage+"/80%positive.csv", patternClass = "miRNA")
fs.add_instances("mohsen/active_hsa1/"+stage+"/80%negative.csv", patternClass = "pseudo")
#active:
fs.select_features([1,18,25,26,34,38,39,43,44,45,139,153,215,216,217,219,220,222,224 ])
fs.libsvm_scale()
fs.export("mohsen/active_hsa1/"+stage+"/80_active_pos.csv", "real")
fs.export("mohsen/active_hsa1/"+stage+"/80_active_neg.csv", "pseudo")
fs.export("mohsen/active_hsa1/"+stage+"/80_active.csv")



numFolds = 10
outPath = "active_learning"
stage=m

posTrainLines = open("mohsen/active_hsa1/"+stage+"/20_active_pos.csv", 'r').readlines()[1:]
negTrainLines = open("mohsen/active_hsa1/"+stage+"/20_active_neg.csv", 'r').readlines()[1:]
#posTrainLines += open("mohsen/dme_cfsselect_positive.csv", 'r').readlines()[1:]
#negTrainLines += open("mohsen/dme_cfsselect_negative.csv", 'r').readlines()[1:]
posTestLines = open("mohsen/active_hsa1/"+stage+"/80_active_pos.csv", 'r').readlines()[1:]
negTestLines = open("mohsen/active_hsa1/"+stage+"/80_active_neg.csv", 'r').readlines()[1:]


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

#allPredictions = sorted(allPredictions, key = lambda x : x[0])

print len(allPredictions)


# Extract ids of pre-processed precursors from the output.mrd file
infile1= open ("mohsen/active_hsa1/"+stage+"/75_ids")
ids = []
for line in infile1:
	ids.append(line.strip()[1:])

# Extract sequences of pre-processed precursors from the precursors.fa file
seqs = {}
getSeq = False
for line in open("mohsen/active_hsa1/precursors.fa"):
	if getSeq == True:
		seq = line.strip()
		#seq = convert_DNA_to_RNA(seq)
		seqs[seqId] = seq
		getSeq = False
	for i in ids:
		if i in line:
			seqId = i
			getSeq = True

with open("mohsen/active_hsa1/tmp1.fa",'w') as outFile:
	for key in seqs.keys():
		outFile.write(">"+key+'\n')
		outFile.write(seqs[key]+'\n')

finalIds = []

for i in ids:
	#if i in hmpHeaders:
	finalIds.append(i)

#TILL HERE


with open("mohsen/active_hsa1/"+stage+"/results/"+outPath+".sresults", 'w') as out:
     for i,p in enumerate(allPredictions):
         # WAS original:
	 #out.write(str(p[0]) + "\t" + str(p[1])+'\t' + p[2] + '\n')
	    #active:
         out.write(finalIds[i]+"\t"+str(p[0]) + "\t" + str(p[1])+ '\n')

ci = float(len(negTestLines)) / float(len(posTestLines))
print "Class imbalance:", ci

spec = 1.0
sens = 0.0
with open("mohsen/active_hsa1/"+stage+"/results/"+outPath+"_roc.tsv", 'w') as out:
    # out.write('1-spec\tsens\tprec\n')
    for p in allPredictions:
        if p[2] == '1':
            sens += float(1)/float(len(posTestLines))
        else:
            spec -= float(1)/float(len(negTestLines))
        out.write(str(1.0-spec)+'\t'+str(sens)+'\t'+str(sens / (sens + (1.0-spec)*ci))+'\n')
