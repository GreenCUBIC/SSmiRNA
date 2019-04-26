from subprocess import call
import random

class FeatureSet():

	def __init__(self):
		self.names = []
		self.features = []
		self.classes = []

	def get_numpos(self):
		return self.classes.count('real')

	def get_numneg(self):
		return self.classes.count('pseudo')

	def add_instances_from_featureset(self, inFeatureset):
		if self.names == []:
			self.names = inFeatureset.names
		for instance in inFeatureset.features:
			self.features.append(instance)
		for instance in inFeatureset.classes:
			self.classes.append(instance)

	def add_instance(self, features, patternClass):
		self.features.append(features)
		self.classes.append(patternClass)

	def get_cv_subsets(self, numSets):
		subsets = []
		numPos = self.classes.count('real')
		numNeg = self.classes.count('pseudo')
		posSet = []
		negSet = []
		for i in range(len(self.features)):
			if self.classes[i] == 'real':
				posSet.append(self.features[i])
			else:
				negSet.append(self.features[i])
		posRemaining = range(numPos)
		negRemaining = range(numNeg)
		for i in range(numSets-1):
			newSet = FeatureSet()
			newSet.names = self.names
			posIndices = random.sample(posRemaining, numPos/numSets)
			negIndices = random.sample(negRemaining, numNeg/numSets)
			for j in posIndices:
				posRemaining.remove(j)
				newSet.add_instance(posSet[j], 'real')
			for j in negIndices:
				negRemaining.remove(j)
				newSet.add_instance(negSet[j], 'pseudo')
			subsets.append(newSet)

		newSet = FeatureSet()
		for j in posRemaining:
			newSet.add_instance(posSet[j], 'real')
		for j in negRemaining:
			newSet.add_instance(negSet[j], 'pseudo')
		subsets.append(newSet)
		return subsets

	def libsvm_scale(self, min='-1', max='+1', params='', paramOut = ''):
		self.export_svm('tmp.libsvm')
		cmd = 'progs/libsvm-3.14/svm-scale'
		if paramOut != '':
			cmd += ' -s '+paramOut
		if params != '':
			cmd += ' -r '+params
		else:
			cmd += ' -l '+min+' -u '+max
		cmd += ' tmp.libsvm > tmp.scale.libsvm'
		print cmd
		call(cmd, shell=True)
		self.load_svm('tmp.scale.libsvm')
		# call('rm tmp.libsvm', shell=True)
		# call('rm tmp.scale.libsvm', shell=True)

	def weka_smote(self):
		numPos = self.classes.count('real')
		numNeg = self.classes.count('pseudo')
		print "NumPos: ", numPos, "NumNeg:", numNeg
		self.export_arff('tmp.arff')
		call('java -Djava.util.Arrays.useLegacyMergeSort=true -classpath progs/weka-3-6-9/weka.jar weka.filters.supervised.instance.SMOTE -C 0 -K 5 -P '+str(((float(self.get_numneg())/float(self.get_numpos()))*100)-100)+' -S 1 -i tmp.arff -o tmpsmote.arff -c "last"', shell=True)
		self.load_arff('tmpsmote.arff')

	def select_features(self, featureNums):
		print "number of features before:",len(self.features[0]) 
		newNames = []
		newFeatures = []
		for fNum in featureNums:
			newNames.append(self.names[fNum])
		
		for pattern in self.features:
			newPattern = []
			for fNum in featureNums:
				newPattern.append(pattern[fNum])
			newFeatures.append(newPattern)

		self.features = newFeatures
		self.names = newNames
		print "number of features after:",len(self.features[0]) 
		print self.names
		print self.features[0]


	def load(self, inPath, patternClass='real'):
		extension = inPath.split('.')[-1]
		if extension in ['arff']:
			self.load_arff(inPath)
		if extension in ['svm', 'libsvm']:
			self.load_svm(inPath)
		if extension in ['features', 'micropred', 'huntmi']:
			self.load_micropred(inPath, patternClass)
		if extension in ['csv', 'hmp', 'hmp20']:
			self.load_csv(inPath)
		print len(self.features)
	def load_micropred(self, inPath, patternClass='real'):
		self.classes = []
		self.names = []
		self.features = []
		for line in open(inPath, 'r').readlines():
			self.features.append([])
			for datum in line.split():
				self.features[-1].append(datum)
		self.names = ["feat"+str(i) for i in range(len(self.features[0]))]
		for i in range(len(self.features)):
			self.classes.append(patternClass)
		return
	def load_arff(self, inPath):
		self.classes = []
		self.names = []
		self.features = []
		lines = open(inPath, 'r').readlines()
		for line in lines:
			if len(line) > 2:
				if line.split()[0] == '@attribute':
					self.names.append(line.split()[1].strip())
				elif line[0] in '@% \n':
					continue
				else:
					self.classes.append(line.split(',')[-1].strip("' \n"))
					self.features.append(line.split(',')[:-1])
		self.names = self.names[:-1]
		return
	def load_svm(self, inPath):
		self.classes = []
		self.names = []
		self.features = []
		lines = open(inPath, 'r').readlines()
		numFeatures = max([int(line.split()[-1].split(':')[0]) for line in lines])
		for line in lines:
			if ':' not in line.split()[0] and line[0] in '0-': 
				self.classes.append('pseudo')
			else:
				self.classes.append('real')
			self.features.append(['0.0' for i in range(numFeatures)])
			for datum in line.split():
				if ':' in datum:
					self.features[-1][int(datum.split(':')[0])-1] = datum.split(':')[1]
		self.names = ["feat"+str(i) for i in range(numFeatures)]
		return
	def load_csv(self, inPath):
		self.classes = []
		self.names = []
		self.features = []
		lines = open(inPath, 'r').readlines()
		# Check for a header line. If there is a header, use it for feature names
		if lines[0][0] in '\"\'':
			self.names = [s.strip('\"\' ') for s in lines[0].split(',')]
			lines = lines[1:]
		# If there is no header, generate default feature names
		else:
			self.names = ["feat"+str(i) for i in range(len(lines[0].split(',')[:-1]))]
		for line in lines:
			if line.split(',')[-1].strip('" \n') in ['miRNA', 'real']:
				self.classes.append('real')
			else:
				self.classes.append('pseudo')
			# self.classes.append(line.split(',')[-1].strip('" \n'))
			self.features.append(line.split(',')[:-1])
		return

	def add_instances(self, inPath, patternClass='real'):
		extension = inPath.split('.')[-1]
		if extension in ['arff']:
			self.add_instances_from_arff(inPath)
		if extension in ['svm', 'libsvm']:
			self.add_instances_from_svm(inPath)
		if extension in ['features', 'micropred', 'huntmi']:
			self.add_instances_from_micropred(inPath, patternClass)
		if extension in ['csv', 'hmp', 'hmp20']:
			self.add_instances_from_csv(inPath)
	def add_instances_from_micropred(self, inPath, patternClass='real'):
		lines = open(inPath, 'r').readlines()
		if len(lines[0].split()) != len(self.features[0]):
			print "Error adding instances to feature set: Expected", str(len(self.features[0])), "features, found", str(len(lines[0].split())), "."
			return
		for line in lines:
			self.features.append([])
			for datum in line.split():
				self.features[-1].append(datum)
			self.classes.append(patternClass)
		return
	def add_instances_from_arff(self, inPath):
		return
	def add_instances_from_svm(self, inPath):
		return
	def add_instances_from_csv(self, inPath, patternClass='real'):
		lines = open(inPath, 'r').readlines()
		if len(lines[0].split(',')) != len(self.features[0])+1:
			print "Error adding instances from "+inPath+" to feature set: Expected", str(len(self.features[0])), "features, found", str(len(lines[0].split())), "."
			return
		if lines[0][0] not in "\'\"":
			self.classes.append(lines[0].split(',')[-1].strip('" \n'))
			self.features.append(lines[0].split(',')[:-1])
		for line in lines[1:]:
			self.classes.append(line.split(',')[-1].strip('" \n'))
			self.features.append(line.split(',')[:-1])
		return

	def add_features(self, inPath):
		extension = inPath.split('.')[-1]
		if extension in ['arff']:
			self.add_features_from_arff(inPath)
		if extension in ['svm', 'libsvm']:
			self.add_features_from_svm(inPath)
		if extension in ['features', 'micropred', 'huntmi']:
			self.add_features_from_micropred(inPath)
		if extension in ['csv', 'hmp', 'hmp20']:
			self.add_features_from_csv(inPath)
	def add_features_from_micropred(self, inPath):
		lines = open(inPath, 'r').readlines()
		numNewFeats = len(lines[0].split())
		numOldFeats = len(self.names)
		for i in range(numNewFeats):
			self.names.append("feat"+str(numOldFeats+i))
		if len(lines) != len(self.features):
			print "Error adding features to feature set: Expected", str(len(self.features[0])), "instances, found", str(len(lines[0].split())), "."
			return
		for i in range(len(lines)):
			for datum in lines[i].split():
				self.features[i].append(datum.strip())
		return
	def add_features_from_arff(self, inPath):
		return
	def add_features_from_svm(self, inPath):
		return
	def add_features_from_csv(self, inPath):
		return

	def export(self, outPath, patternClass='all'):
		extension = outPath.split('.')[-1]
		if extension in ['arff']:
			self.export_arff(outPath)
		if extension in ['svm', 'libsvm']:
			self.export_svm(outPath, patternClass)
		if extension in ['features', 'micropred', 'huntmi']:
			self.export_micropred(outPath)
		if extension in ['csv', 'hmp', 'hmp20']:
			self.export_csv(outPath, patternClass)
	def export_micropred(self, outPath):
		with open(outPath, 'w') as outFile:
			for featSet in self.features:
				for feat in featSet[:-1]:
					outFile.write(feat+'  ')
				outFile.write(featSet[-1]+'\n')
		return
	def export_arff(self, outPath):
		with open(outPath, 'w') as outFile:
			outFile.write("@relation 'miRNA'\n")
			for attr in self.names:
				outFile.write('@attribute '+attr+' real\n')
			outFile.write("@attribute class {'real', 'pseudo'}\n")
			outFile.write('@data\n')
			for i in range(len(self.features)):
				for feat in self.features[i]:
					outFile.write(feat+',')
				outFile.write("'"+self.classes[i]+"'\n")
		return
	def export_svm(self, outPath, patternClass='all'):
		with open(outPath, 'w') as outFile:
			for i in range(len(self.features)):
				if self.classes[i] == patternClass or patternClass == 'all':
					if self.classes[i] in ['real', 'miRNA']:
						outFile.write('1 ')
					else:
						outFile.write('0 ')
					for j in range(len(self.features[i])):
						if self.features[i][j] != '0.0':
							outFile.write(str(j+1) + ':' +self.features[i][j]+' ')
					outFile.write('\n')
		return
	def export_csv(self, outPath, patternClass='all'):
		with open(outPath, 'w') as outFile:
			for attr in self.names:
				outFile.write('"'+attr+'",')
			outFile.write('"class"\n')
			for i in range(len(self.features)):
				if self.classes[i] == patternClass or patternClass == 'all':
					for feat in self.features[i]:
						outFile.write(feat+',')
					outFile.write('"'+self.classes[i]+'"\n')
		return

# Example usage
# fs = FeatureSet()
# fs.load("../data/dps_positive.fasta.huntmi", patternClass = 'real')
# fs.add_instances("../data/dps_negative.fasta.huntmi", patternClass = 'pseudo')
# fs.export("../data/dps_all.arff")
