import numpy as np
import pandas as pd
import random
import sys
from collections import Counter


class DecisionTree:
    def __init__(self, max_depth=10, min_samples_split=5):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None

    def gini(self, y):
        classes = np.unique(y)
        impurity = 1
        for c in classes:
            p = np.sum(y == c) / len(y)
            impurity -= p ** 2
        return impurity

    def split_data(self, X, y, feature, threshold):
        left_mask = X[:, feature] <= threshold
        right_mask = X[:, feature] > threshold
        return X[left_mask], y[left_mask], X[right_mask], y[right_mask]

    def best_split(self, X, y):
        best_feature, best_thresh, best_gini = None, None, float("inf")

        n_features = X.shape[1]
        features = random.sample(range(n_features), int(np.sqrt(n_features)))

        for feature in features:
            thresholds = np.unique(X[:, feature])
            for t in thresholds:
                _, y_left, _, y_right = self.split_data(X, y, feature, t)
                if len(y_left) == 0 or len(y_right) == 0:
                    continue

                gini_split = (len(y_left) * self.gini(y_left) + 
                              len(y_right) * self.gini(y_right)) / len(y)

                if gini_split < best_gini:
                    best_gini = gini_split
                    best_feature = feature
                    best_thresh = t

        return best_feature, best_thresh

    def build_tree(self, X, y, depth=0):
        if len(set(y)) == 1 or depth >= self.max_depth or len(y) < self.min_samples_split:
            return Counter(y).most_common(1)[0][0]

        feature, threshold = self.best_split(X, y)
        if feature is None:
            return Counter(y).most_common(1)[0][0]

        X_left, y_left, X_right, y_right = self.split_data(X, y, feature, threshold)

        return {
            "feature": feature,
            "threshold": threshold,
            "left": self.build_tree(X_left, y_left, depth + 1),
            "right": self.build_tree(X_right, y_right, depth + 1)
        }

    def fit(self, X, y):
        self.tree = self.build_tree(X, y)

    def predict_one(self, x, tree):
        if not isinstance(tree, dict):
            return tree
        if x[tree["feature"]] <= tree["threshold"]:
            return self.predict_one(x, tree["left"])
        else:
            return self.predict_one(x, tree["right"])

    def predict(self, X):
        return np.array([self.predict_one(x, self.tree) for x in X])


class RandomForest:
    def __init__(self, n_trees=50, max_depth=12):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.trees = []

    def bootstrap(self, X, y):
        idxs = np.random.choice(len(X), len(X), replace=True)
        return X[idxs], y[idxs]

    def fit(self, X, y):
        self.trees = []
        for i in range(self.n_trees):
            X_sample, y_sample = self.bootstrap(X, y)
            tree = DecisionTree(max_depth=self.max_depth)
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)
            self.progress_bar(i+1,self.n_trees,"🌳 Training Tree")
            # print(f"🌳 Tree {i+1}/{self.n_trees} trained")
    
    def predict(self, X):
        tree_preds = np.array([tree.predict(X) for tree in self.trees])
        return np.array([Counter(tree_preds[:, i]).most_common(1)[0][0] for i in range(len(X))])

    def predict_proba(self, X):
        tree_preds = np.array([tree.predict(X) for tree in self.trees])
        probs = []

        for i in range(len(X)):
            counts = Counter(tree_preds[:, i])
            total = sum(counts.values())
            prob = [counts.get(0, 0)/total, counts.get(1, 0)/total]
            probs.append(prob)

        return np.array(probs)
    
    def progress_bar(self,progress, total,message="",bar_length=40):
        fraction = progress / total
        arrow = int(fraction * bar_length) * '='
        padding = (bar_length - len(arrow)) * '-'

        bar = f"{message} [{arrow}>{padding}] {int(fraction * 100)}%"

        sys.stdout.write("\r" + bar)
        sys.stdout.flush()


class NoiseFilter:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)

        self.df["width"] = self.df["max_x"] - self.df["min_x"]
        self.df["height"] = self.df["max_y"] - self.df["min_y"]
        self.df["area"] = self.df["width"] * self.df["height"]
        self.df["center_x"] = (self.df["min_x"] + self.df["max_x"]) / 2
        self.df["center_y"] = (self.df["min_y"] + self.df["max_y"]) / 2

        self.features = [
            "min_x","min_y","max_x","max_y",
            "width","height","area","center_x","center_y"
        ]

        self.X = self.df[self.features].values
        self.y = self.df["label"].values

        self.model = RandomForest(n_trees=50, max_depth=12)

    def train(self):
        print("Training Random Forest from scratch...")
        self.model.fit(self.X, self.y)

    def predict_box(self, min_x, min_y, max_x, max_y):
        width = max_x - min_x
        height = max_y - min_y
        area = width * height
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        sample = np.array([[min_x,min_y,max_x,max_y,width,height,area,center_x,center_y]])

        pred = self.model.predict(sample)[0]
        prob = self.model.predict_proba(sample)[0]

        return pred, prob

# rf = NoiseRFManual("merged_classification.csv")
# rf.train()

# pred, prob = rf.predict_box(100,120,150,190)
# print("Prediction:", pred)
# print("Probabilities:", prob)
