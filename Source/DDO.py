from surrogate_model.GPRs import GPRs
import pandas as pd
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, RBF
import numpy as np

class DDO(): # Data-Driven Optimization
    def __init__(self, file_name = 'LHS180_t1.xlsx'):
        self.read_excel(file_name)

    def read_excel(self, file_name = 'LHS180_t1.xlsx'):
        df_info = pd.read_excel(file_name, "info").fillna(np.nan).replace([np.nan], [None])
        df = pd.read_excel(file_name, "conv")
        self.QoI_direction = np.ones(len(df_info["QoI"]))
        for idx, (min, max) in enumerate(zip(df_info["minimize"], df_info["maximize"])):
            if (min is None) and (max is not None): # if maximization, direction = -1
                self.QoI_direction[idx] = -1.
            elif (min is not None) and (max is None): # if minimization, direction = +1
                pass
            elif (min is None) and (max is None): # error: neither max nor min
                raise Exception(f"Max/Min should be determined for {df_info['QoI'][idx]}")
            elif (min is not None) and (max is not None): # error: neither max nor min
                raise Exception(f"Max/Min cannot be performed simultaneously for {df_info['QoI'][idx]}")

        x_num = sum(word.count("DV") for word in list(df.columns)) # Number of design variables (calculated by how many times "DV" appeared in the indices' name)
        self.x_list = ["DV"+f"{i}" for i in range(x_num)]
        self.y_list = list(df_info["QoI"])
        self.train_size = int(df.shape[0] * 0.8) # 80% for the train data

        x = df[self.x_list].to_numpy()
        y = df[self.y_list].to_numpy()

        self.x, self.y = x, y
        self.n_var = self.x.shape[1]
        self.n_obj = self.y.shape[1]


    def shuffle(self, rand_seed=42):

        np.random.seed(rand_seed)
        # Data shuffling
        random_idx = np.arange(self.x.shape[0])
        np.random.shuffle(random_idx)
        x_shuffled, y_shuffled = self.x[random_idx], self.y[random_idx]

        # Train-Test split
        self.x_train, self.y_train = x_shuffled[:self.train_size], y_shuffled[:self.train_size]
        self.x_test, self.y_test = x_shuffled[self.train_size:], y_shuffled[self.train_size:]

        # Manual elimination of outliers
        self.x_train = np.delete(self.x_train, [14,50], axis=0)
        self.y_train = np.delete(self.y_train, [14,50], axis=0)

    def fit(self, **kwargs):

        kernel = ConstantKernel() * Matern(length_scale=[1.]*self.n_var, nu=2.5)
        # kernel = ConstantKernel() * RBF(length_scale=[1.]*self.n_var)
        # kernel = ConstantKernel() * RBF(length_scale=1.)
        self.gpr_models = GPRs(**kwargs)
        self.gpr_models.fit(self.x_train, self.y_train)

    def predict(self, x=None, return_std=False):

        if x is None: # When the x for the prediction is not given, perform prediction with x_test datatset
            y_pred = self.gpr_models.predict(self.x_test, return_std=return_std)
        else:
            y_pred = self.gpr_models.predict(x, return_std=return_std)

        return y_pred

