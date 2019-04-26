# SSmiRNA
Semi-supervised machine learning integrated pipeline for miRNA prediction. Accompanies "A Semi-Supervised Machine Learning Framework 
for MicroRNA Prediction" manuscript by Mohsen Sheikh Hassani &amp; James R. Green
The "pipeline.py" file demonstrates the general framework of the multi-view co-training process. During each learning iteration, the top two positive and negative instances predicted by one view are added to the initial training set of the other view. 
"Featureset.py", written by Rob Peace, extracts the sequence and expression-based features. 
"Smote.py" is used for class imbalance correction.

